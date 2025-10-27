from flask import Blueprint, render_template, request, jsonify, session, current_app
# Assuming 'app' contains the SQLAlchemy 'db' object and models
from app import db 
from app.models import Conversation, User, Warehouse, Product, Order, ChatSession
from app.database_service import DatabaseService
from app.llm_classification_service import LLMClassificationService
from app.web_search_service import WebSearchService
from app.order_service import OrderService
from app.enhanced_order_service import EnhancedOrderService
from app.groq_service import GroqService 
from app.email_utils import send_conversation_email 
import logging
from datetime import datetime

chatbot_bp = Blueprint('chatbot', __name__)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
db_service = None
classification_service = None
web_search_service = None
order_service = None
enhanced_order_service = None
llm_service = None

# --- Helper Functions to get service instances ---
def get_db_service():
    """Get database service instance"""
    global db_service
    if db_service is None:
        db_service = DatabaseService()
    return db_service

def get_classification_service():
    """Get LLM classification service instance"""
    global classification_service
    if classification_service is None:
        classification_service = LLMClassificationService()
    return classification_service

def get_web_search_service():
    """Get web search service instance"""
    global web_search_service
    if web_search_service is None:
        web_search_service = WebSearchService()
    return web_search_service

def get_order_service():
    """Get order service instance"""
    global order_service
    if order_service is None:
        order_service = OrderService()
    return order_service

def get_enhanced_order_service():
    """Get enhanced order service instance"""
    global enhanced_order_service
    if enhanced_order_service is None:
        enhanced_order_service = EnhancedOrderService()
    return enhanced_order_service

def get_llm_service():
    """Get LLM service instance (GroqService)"""
    global llm_service
    if llm_service is None:
        llm_service = GroqService()
    return llm_service

def reset_order_session():
    """Reset order session to initial state"""
    return {
        'status': 'idle',  # idle, browsing, calculating, confirming, completed
        'items': [],
        'total_cost': 0,
        'discount_applied': 0,
        'final_total': 0,
        'order_id': None
    }

def reset_tracking_session():
    """Reset tracking session to initial state"""
    return {
        'status': 'idle',  # idle, selecting, viewing, completed
        'selected_order_id': None,
        'order_details': None,
        'available_orders': []
    }

@chatbot_bp.route('/')
def chat():
    """Chat interface"""
    # Assuming current_user exists in the context
    return render_template('chat.html', user=None) 

@chatbot_bp.route('/message', methods=['POST'])
def process_message():
    """Process chat message with Quantum Blue logic"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # --- Quantum Blue Onboarding Flow ---
        if 'onboarding_state' not in session:
            session['onboarding_state'] = 'ask_name'

        state = session['onboarding_state']

        if 'onboarding' not in session:
            session['onboarding'] = {}

        # Onboarding states
        if state == 'ask_name':
            session['onboarding_state'] = 'get_name'
            return jsonify({'response': 'Hi — what\'s your name?'}), 200

        if state == 'get_name':
            session['onboarding']['name'] = user_message[:100]
            session['onboarding_state'] = 'ask_email'
            return jsonify({'response': 'Thanks! Please share your email id.'}), 200

        if state == 'ask_email':
            session['onboarding']['email'] = user_message[:120]
            session['onboarding_state'] = 'ask_phone'
            return jsonify({'response': 'Got it. What is your phone number?'}), 200

        if state == 'ask_phone':
            session['onboarding']['phone'] = user_message[:50]
            name = session['onboarding']['name']
            email = session['onboarding']['email']
            phone = session['onboarding']['phone']

            # Check if user exists
            db_service = get_db_service()
            user = db_service.get_user_by_email(email)
            if not user:
                user = db_service.create_user(name, email, phone)

            otp = user.generate_otp()
            db.session.commit()

            from app.email_utils import send_otp_email
            send_otp_email(email, name, otp)

            session['onboarding_state'] = 'await_otp'
            return jsonify({'response': 'We have sent an OTP to your email. Please enter the 6-digit OTP to verify.'}), 200

        if state == 'await_otp':
            email = session['onboarding']['email']
            db_service = get_db_service()
            user = db_service.get_user_by_email(email)
            if not user or not user.verify_otp(user_message, expiration=current_app.config.get('OTP_EXPIRATION', 600)):
                return jsonify({'response': 'Invalid or expired OTP. Please try again.'}), 200

            user.verify_email()
            db.session.commit()

            session['onboarding_state'] = 'ask_warehouse'
            warehouses = db_service.get_warehouses()
            warehouse_options = [w.location_name for w in warehouses]
            return jsonify({
                'response': 'Email verified successfully! What\'s your warehouse location?',
                'warehouse_options': warehouse_options
            }), 200

        if state == 'ask_warehouse':
            warehouse_location = user_message
            email = session['onboarding']['email']
            db_service = get_db_service()
            user = db_service.get_user_by_email(email)
            
            if user:
                user.warehouse_location = warehouse_location
                user.last_verification = datetime.utcnow()
                db.session.commit()
                
                session['onboarding_state'] = 'completed'
                session['user_id'] = user.id
                session['warehouse_location'] = warehouse_location
                
                # Create chat session
                chat_session = db_service.create_chat_session(user.id)
                session['session_id'] = chat_session.session_id
                
                return jsonify({
                    'response': 'Perfect! Your warehouse location has been set. Would you like to place an order, track an order, or learn about our company or ask something else?'
                }), 200
            else:
                return jsonify({'response': 'Error setting warehouse location. Please try again.'}), 200

        # --- Main Chat Flow (Verified User) ---
        session_user_id = session.get('user_id')
        if not session_user_id:
            return jsonify({'response': 'Please complete the onboarding process first.'}), 200

        # Get services
        db_service = get_db_service()
        classification_service = get_classification_service()
        web_search_service = get_web_search_service()
        order_service = get_order_service()
        llm_service = get_llm_service()

        # Get user context
        user = User.query.get(session_user_id)
        warehouse_location = session.get('warehouse_location')
        
        # Get user's warehouse
        warehouse = db_service.get_warehouse_by_location(warehouse_location)
        context_data = {
            'user_warehouse': warehouse_location,
            'user_email': user.email
        }

        # Get recent orders for context
        recent_orders = db_service.get_orders_by_email(user.email)
        context_data['recent_orders'] = recent_orders[:3]  # Last 3 orders
        
        # Initialize or get order session data with enhanced state management
        if 'order_session' not in session:
            session['order_session'] = {
                'status': 'idle',  # idle, browsing, calculating, confirming, completed
                'items': [],
                'total_cost': 0,
                'discount_applied': 0,
                'final_total': 0,
                'order_id': None,
                'cart_id': None,
                'last_updated': datetime.utcnow().isoformat(),
                'user_selections': [],
                'pending_confirmation': False
            }
        
        # Initialize or get tracking session data
        if 'tracking_session' not in session:
            session['tracking_session'] = {
                'status': 'idle',  # idle, selecting, viewing, completed
                'selected_order_id': None,
                'order_details': None,
                'available_orders': []
            }
        
        order_session = session['order_session']
        tracking_session = session['tracking_session']

        # 1. Classify user intent using LLM
        classification_result = classification_service.classify_user_intent(user_message, context_data)
        intent = classification_result.get('classification', 'OTHER')
        
        logger.info(f"Intent classified as: {intent}")
        logger.info(f"Order session status: {order_session['status']}")
        logger.info(f"Order session items: {len(order_session['items'])}")

        # 2. Process based on classification
        if intent == 'CALCULATE_COST' or 'add' in user_message.lower():
            # Handle adding products to cart - enhanced to handle all states
            if 'add' in user_message.lower():
                # If order session is not in the right state, initialize it
                if order_session['status'] not in ['confirming', 'calculating']:
                    order_session['status'] = 'confirming'
                    order_session['pending_confirmation'] = True
                    session['order_session'] = order_session
                
                # Load products from warehouse for product matching
                products = []
                if warehouse:
                    products = db_service.get_products_by_warehouse(warehouse.id)
                
                # Parse add product request with enhanced pattern matching
                import re
                add_patterns = [
                    r'add\s+(\d+)\s+(.+?)(?:\s+to\s+cart)?$',
                    r'add\s+(.+?)\s+(\d+)(?:\s+to\s+cart)?$',
                    r'add\s+(.+?)$'
                ]
                
                added_items = []
                for pattern in add_patterns:
                    match = re.search(pattern, user_message.lower())
                    if match:
                        if len(match.groups()) == 2:
                            if match.group(1).isdigit():
                                quantity = int(match.group(1))
                                product_name = match.group(2).strip()
                            else:
                                quantity = int(match.group(2))
                                product_name = match.group(1).strip()
                        else:
                            quantity = 1
                            product_name = match.group(1).strip()
                        
                        # Enhanced product matching with better logic
                        product = None
                        product_name_lower = product_name.lower()
                        
                        # Try exact matches first
                        for p in products:
                            if (product_name_lower == p.product_name.lower() or 
                                product_name_lower == p.product_code.lower()):
                                product = p
                                break
                        
                        # Try partial matches if exact match fails
                        if not product:
                            for p in products:
                                if (product_name_lower in p.product_name.lower() or 
                                    p.product_code.lower() in product_name_lower or
                                    any(word in p.product_name.lower() for word in product_name_lower.split() if len(word) > 2)):
                                    product = p
                                    break
                        
                        if product:
                            logger.info(f"Product found: {product.product_name} ({product.product_code})")
                            # Calculate pricing
                            pricing_info = db_service.get_product_pricing(product.id, quantity)
                            
                            # Add to existing cart or create new item
                            existing_item = None
                            for item in order_session['items']:
                                if item['product_code'] == product.product_code:
                                    existing_item = item
                                    break
                            
                            if existing_item:
                                # Update existing item
                                existing_item['quantity'] += quantity
                                existing_item['item_total'] += pricing_info['total_amount']
                                logger.info(f"Updated existing item: {product.product_name}")
                            else:
                                # Add new item
                                new_item = {
                                    'product_name': product.product_name,
                                    'product_code': product.product_code,
                                    'quantity': quantity,
                                    'unit_price': pricing_info['base_price'],
                                    'final_price': pricing_info['final_price'],
                                    'discount_percentage': pricing_info['discount_percentage'],
                                    'scheme_name': pricing_info['scheme_name'],
                                    'item_total': pricing_info['total_amount']
                                }
                                order_session['items'].append(new_item)
                                logger.info(f"Added new item: {product.product_name}")
                            
                            # Update totals
                            order_session['total_cost'] += pricing_info['total_amount']
                            order_session['final_total'] += pricing_info['total_amount']
                            session['order_session'] = order_session
                            
                            added_items.append({
                                'name': product.product_name,
                                'quantity': quantity,
                                'total': pricing_info['total_amount']
                            })
                        else:
                            logger.warning(f"Product not found for: {product_name}")
                        break
                
                if added_items:
                    # Create updated cart summary
                    cart_summary = "**Updated Cart:**\n\n"
                    for item in order_session['items']:
                        cart_summary += f"📦 {item['product_name']} - {item['quantity']} units - ${item['item_total']:,.2f}\n"
                    
                    response = f"""✅ **Products Added to Cart!**

{cart_summary}

💰 **New Total: ${order_session['final_total']:,.2f}**

**Updated Order Calculations:**

"""
                    
                    for item in order_session['items']:
                        response += f"""**{item['product_name']} (QB{item['product_code'][2:]})**
   • Quantity: {item['quantity']} units
   • Base Price: ${item['unit_price']:,.2f} each
   • Discount: {item['discount_percentage']:.1f}% off
   • Final Price: ${item['final_price']:,.2f} each
   • Scheme: {item['scheme_name']}
   • Item Total: ${item['item_total']:,.2f}

"""
                    
                    response += f"""💰 **Total Order Amount: ${order_session['final_total']:,.2f}**

**🎯 Recommended Add-ons:**

1. **Quantum Sensors (QB004)** - $1,800.00
   - Perfect companion for Quantum Processors
   - Scheme: Buy 1 Get 15% Off

2. **Neural Network Module (QB002)** - $1,200.00  
   - Enhances AI Controller performance
   - Scheme: Buy 1 Get 20% Off

3. **AI Memory Card (QB003)** - $800.00
   - Additional storage for your AI systems
   - Scheme: Buy 3 Get 2 Free

**📝 Next Steps:**
• Type 'add [product name]' to include additional items
• Type 'place order' to finalize your current selection
• Type 'remove [product name]' to remove items

Would you like to add more products or proceed with your order?"""
                    
                else:
                    # Get available products for better error message
                    available_products = []
                    for p in products:
                        available_products.append(f"• {p.product_name} ({p.product_code})")
                    
                    response = f"""I apologize, but I couldn't identify the specific product you want to add. 

To help you better, please use one of these formats:
• 'add 2 Quantum Sensors'
• 'add Neural Network Module' 
• 'add 1 AI Memory Card'

**Available Products:**
{chr(10).join(available_products)}

**Debug Info:**
• You said: "{user_message}"
• Order session status: {order_session['status']}
• Current cart items: {len(order_session['items'])}

Please try again with the exact product name, and I'll be happy to add it to your order!"""
                
                return jsonify({
                    'response': response,
                    'intent': 'ADD_TO_CART',
                    'confidence': 0.9
                }), 200
            
            # Handle removing products from cart
            elif 'remove' in user_message.lower() and order_session['status'] in ['confirming', 'calculating']:
                import re
                remove_patterns = [
                    r'remove\s+(.+?)$',
                    r'delete\s+(.+?)$'
                ]
                
                removed_items = []
                for pattern in remove_patterns:
                    match = re.search(pattern, user_message.lower())
                    if match:
                        product_name = match.group(1).strip()
                        
                        # Find matching item in cart
                        item_to_remove = None
                        for item in order_session['items']:
                            if (product_name.lower() in item['product_name'].lower() or 
                                product_name.upper() in item['product_code']):
                                item_to_remove = item
                                break
                        
                        if item_to_remove:
                            # Remove from cart
                            order_session['items'].remove(item_to_remove)
                            order_session['total_cost'] -= item_to_remove['item_total']
                            order_session['final_total'] -= item_to_remove['item_total']
                            session['order_session'] = order_session
                            
                            removed_items.append(item_to_remove['product_name'])
                        break
                
                if removed_items:
                    if order_session['items']:
                        # Create updated cart summary
                        cart_summary = "**Updated Cart:**\n\n"
                        for item in order_session['items']:
                            cart_summary += f"📦 {item['product_name']} - {item['quantity']} units - ${item['item_total']:,.2f}\n"
                        
                        response = f"""✅ **Products Removed from Cart!**

{cart_summary}

💰 **New Total: ${order_session['final_total']:,.2f}**

**Next Steps:**
• Type 'add [product name]' to include more items
• Type 'place order' to finalize your selection"""
                    else:
                        response = "✅ **Cart Cleared!**\n\nYour cart is now empty. Would you like to browse our products?"
                        order_session['status'] = 'idle'
                        session['order_session'] = order_session
                else:
                    response = "I couldn't find that product in your cart. Please check the product name and try again."
                
                return jsonify({
                    'response': response,
                    'intent': 'REMOVE_FROM_CART',
                    'confidence': 0.9
                }), 200
        
        if intent == 'CALCULATE_COST':
            # Get products from user's warehouse
            if warehouse:
                products = db_service.get_products_by_warehouse(warehouse.id)
                
                # Get recent conversation history for context
                session_id = session.get('session_id')
                conversation_history = []
                if session_id:
                    chat_session = ChatSession.query.filter_by(session_id=session_id).first()
                    if chat_session:
                        conversations = db_service.get_session_conversations(chat_session.session_id)
                        conversation_history = [conv.to_dict() for conv in conversations[-10:]]  # Last 10 conversations
                
                # Calculate order cost
                cost_data = classification_service.calculate_order_cost(user_message, products, conversation_history)
                
                if cost_data.get('order_ready') and cost_data.get('order_items'):
                    # Update order session with calculated data
                    order_session['status'] = 'calculating'
                    order_session['items'] = cost_data['order_items']
                    order_session['total_cost'] = cost_data['subtotal']
                    order_session['discount_applied'] = cost_data['discount_amount']
                    order_session['final_total'] = cost_data['final_total']
                    session['order_session'] = order_session
                    
                    # Format the cost response
                    items_text = ""
                    for item in cost_data['order_items']:
                        items_text += f"• {item['product_name']} (QB{item['product_code'][2:]}) - {item['quantity']} units × ${item['unit_price']:,.2f} = ${item['item_total']:,.2f}\n"
                    
                    response = f"""💰 Order Cost Breakdown:

{items_text}
Subtotal: ${cost_data['subtotal']:,.2f}"""
                    
                    if cost_data['discount_amount'] > 0:
                        response += f"""
Discount ({cost_data['discount_percentage']}%): -${cost_data['discount_amount']:,.2f}"""
                    
                    response += f"""

🎯 Final Total: ${cost_data['final_total']:,.2f}

Would you like to proceed with this order?"""
                else:
                    response = "I couldn't identify the specific products you want to order. Could you please specify which products and quantities you're interested in?"
            else:
                response = "I couldn't find your warehouse. Please contact support."
                
        elif intent == 'PLACE_ORDER':
            # Get products from user's warehouse
            if warehouse:
                products = db_service.get_products_by_warehouse(warehouse.id)
                
                # Check if this is a simple order confirmation
                is_simple_confirmation = ('confirm my order' in user_message.lower() or 'process the items in my cart' in user_message.lower()) and not any(product in user_message for product in ['Quantum Processor', 'AI Controller', 'Quantum Sensors', 'AI Memory Card', 'Neural Network Module'])
                
                # Check if this is a detailed order confirmation with pricing
                is_detailed_confirmation = 'I confirm my order with the following details' in user_message
                
                # Check if user is trying to finalize an order
                finalize_keywords = ['finalize', 'proceed', 'confirm', 'place the order', 'place my order', 'place order', 'yes proceed', 'yes it is correct', 'yes', 'ok']
                is_finalizing = any(keyword in user_message.lower() for keyword in finalize_keywords)
                
                # Check if we have order session data
                has_order_session = (order_session['status'] in ['calculating', 'confirming'] and order_session['items']) or (order_session.get('items') and len(order_session['items']) > 0)
                
                # If previous order was completed and user wants to start new order, clear the cart
                if order_session.get('status') == 'completed':
                    logger.info("Previous order completed - force clearing cart for new order")
                    enhanced_order_service = get_enhanced_order_service()
                    enhanced_order_service.force_clear_cart()
                    order_session = session.get('order_session', {})
                    has_order_session = False
                
                logger.info(f"Order processing conditions:")
                logger.info(f"  is_simple_confirmation: {is_simple_confirmation}")
                logger.info(f"  is_detailed_confirmation: {is_detailed_confirmation}")
                logger.info(f"  is_finalizing: {is_finalizing}")
                logger.info(f"  has_order_session: {has_order_session}")
                logger.info(f"  order_session_status: {order_session['status']}")
                logger.info(f"  order_session_items: {len(order_session.get('items', []))}")
                
                # Handle initial order request - show product selection
                if not has_order_session and not is_simple_confirmation and not is_finalizing:
                    # User wants to place order for the first time
                    # If previous order was completed, clear the cart
                    if order_session.get('status') == 'completed':
                        enhanced_order_service = get_enhanced_order_service()
                        enhanced_order_service.force_clear_cart()
                        order_session = session.get('order_session', {})
                    
                    order_session['status'] = 'browsing'
                    session['order_session'] = order_session
                    
                    response = f"""🛒 **Welcome to Quantum Blue Ordering System!**

I'm excited to help you place your order! We have an amazing selection of cutting-edge products available.

**Our Premium Product Line:**
• **Quantum Processor (QB001)** - $2,500.00 - Advanced AI processing power
• **Neural Network Module (QB002)** - $1,200.00 - Enhanced machine learning capabilities  
• **AI Memory Card (QB003)** - $800.00 - High-speed data storage
• **Quantum Sensors (QB004)** - $1,800.00 - Precision measurement technology
• **AI Controller (QB005)** - $950.00 - Intelligent system management

**Special Offers Available:**
🎯 All products come with exclusive discount schemes
🎯 Bulk order discounts available
🎯 Free shipping on orders over $5,000

**How to Order:**
1. Click on the products you want to add to your cart
2. Adjust quantities as needed  
3. Review your order summary with pricing
4. Add more products or proceed to checkout

Let's get started! Please select the products you'd like to order from the options below."""
                    
                    return jsonify({
                        'response': response,
                        'intent': 'PLACE_ORDER',
                        'confidence': 0.9
                    }), 200
                
                # Handle cart confirmation with existing items
                elif is_simple_confirmation and has_order_session:
                    # User wants to confirm their existing cart
                    # Refresh session data to ensure we have the latest cart
                    order_session = session.get('order_session', {})
                    order_items = order_session.get('items', [])
                    total_amount = order_session.get('final_total', 0)
                    
                    logger.info(f"Cart confirmation - Items count: {len(order_items)}")
                    logger.info(f"Cart confirmation - Total amount: {total_amount}")
                    for item in order_items:
                        logger.info(f"Cart item: {item['product_name']} - Qty: {item['quantity']} - Total: {item['item_total']}")
                    
                    # Create professional cart summary
                    cart_summary = "**📋 Your Complete Order Summary:**\n\n"
                    for item in order_items:
                        cart_summary += f"""**{item['product_name']} (QB{item['product_code'][2:]})**
   • Quantity: {item['quantity']} units
   • Base Price: ${item['unit_price']:,.2f} each
   • Discount: {item['discount_percentage']:.1f}% off ({item['scheme_name']})
   • Final Price: ${item['final_price']:,.2f} each
   • Item Total: ${item['item_total']:,.2f}

"""
                    
                    cart_summary += f"""**💰 Total Order Amount: ${total_amount:,.2f}**

**🎯 Recommended Add-ons:**
1. **Quantum Sensors (QB004)** - $1,800.00
   - Perfect companion for Quantum Processors
   - Scheme: Buy 1 Get 15% Off

2. **Neural Network Module (QB002)** - $1,200.00  
   - Enhances AI Controller performance
   - Scheme: Buy 1 Get 20% Off

3. **AI Memory Card (QB003)** - $800.00
   - Additional storage for your AI systems
   - Scheme: Buy 3 Get 2 Free

**📝 Next Steps:**
• Type 'add [product name]' to include additional items
• Type 'place order' to finalize your current selection
• Type 'remove [product name]' to remove items

Would you like to add more products or proceed with your order?"""
                    
                    return jsonify({
                        'response': cart_summary,
                        'intent': 'PLACE_ORDER',
                        'confidence': 0.9
                    }), 200
                
                # Handle order finalization
                elif is_finalizing and has_order_session:
                    # Handle order finalization using existing cart data
                    try:
                        # Use existing order session data
                        order_items = order_session['items']
                        total_amount = order_session.get('final_total', 0)
                        
                        # Create order using the enhanced order service
                        enhanced_order_service = get_enhanced_order_service()
                        
                        # Convert order session items to cart format
                        cart_items = []
                        for item in order_items:
                            cart_items.append({
                                'product_code': item['product_code'],
                                'quantity': item['quantity']
                            })
                        
                        # Create the order
                        order, message = enhanced_order_service.create_order_from_cart(
                            user_id=session_user_id,
                            cart_items=cart_items,
                            warehouse_id=warehouse.id,
                            warehouse_location=warehouse_location,
                            user_email=user.email
                        )
                        
                        if order:
                            # Update order session to completed
                            order_session['status'] = 'completed'
                            order_session['order_id'] = order.order_id
                            session['order_session'] = order_session
                            
                            # Clear the cart after successful order
                            enhanced_order_service.force_clear_cart()
                            
                            response = f"""🎉 **Order Placed Successfully!**

**📋 Order Details:**
• **Order ID:** {order.order_id}
• **Total Amount:** ${order.total_amount:,.2f}
• **Status:** {order.status.title()}
• **Warehouse:** {warehouse_location}
• **Order Date:** {order.order_date.strftime('%B %d, %Y at %I:%M %p')}

**🛍️ Order Summary:**

"""
                            
                            for item in order_items:
                                response += f"""**{item['product_name']} (QB{item['product_code'][2:]})**
   • Quantity: {item['quantity']} units
   • Final Price: ${item['final_price']:,.2f} each
   • Item Total: ${item['item_total']:,.2f}

"""
                            
                            response += f"""**💰 Total Order Amount: ${order.total_amount:,.2f}**

**📧 Confirmation Email Sent**
Your order confirmation has been sent to {user.email}. Please check your inbox for detailed order information and tracking details.

**🚀 What's Next?**
• You'll receive email updates as your order progresses
• Use Order ID **{order.order_id}** to track your order
• Our team will process your order within 24 hours
• Expected delivery: 3-5 business days

**💎 Thank you for choosing Quantum Blue!**
We're excited to deliver cutting-edge technology to you. If you have any questions, feel free to ask!"""
                        else:
                            response = f"❌ Order failed: {message}"
                            
                        return jsonify({
                            'response': response,
                            'intent': 'PLACE_ORDER',
                            'confidence': 0.95
                        }), 200
                        
                    except Exception as e:
                        logger.error(f"Error processing order finalization: {str(e)}")
                        return jsonify({
                            'response': "I apologize, but I couldn't process your order. Please try again or contact support.",
                            'intent': 'PLACE_ORDER',
                            'confidence': 0.5
                        }), 200
                
                
                # Handle simple product listing (e.g., "Quantum Processor - 3 units")
                if not is_detailed_confirmation and not is_simple_confirmation:
                    # Try to parse simple product listings
                    try:
                        import re
                        
                        # Define product mappings
                        product_mappings = {
                            'QB001': 'Quantum Processor',
                            'QB002': 'Neural Network Module', 
                            'QB003': 'AI Memory Card',
                            'QB004': 'Quantum Sensors',
                            'QB005': 'AI Controller'
                        }
                        
                        # Parse simple product listings like "Quantum Processor - 3 units"
                        order_items = []
                        total_amount = 0
                        
                        logger.info(f"Parsing order from user message: {user_message}")
                        
                        # Try to match product names with quantities
                        for product_code, product_name in product_mappings.items():
                            # Pattern to match "Product Name - X units" or "X Product Name"
                            patterns = [
                                rf'{re.escape(product_name)}\s*-\s*(\d+)\s*units?',
                                rf'(\d+)\s*{re.escape(product_name)}',
                                rf'{re.escape(product_name)}\s*(\d+)',
                                rf'(\d+)\s*{re.escape(product_name)}'
                            ]
                            
                            logger.info(f"Trying to match product: {product_name} ({product_code})")
                            
                            for i, pattern in enumerate(patterns):
                                match = re.search(pattern, user_message, re.IGNORECASE)
                                if match:
                                    quantity = int(match.group(1))
                                    logger.info(f"Found match for {product_name}: {quantity} units (pattern {i+1})")
                                    
                                    # Get product details
                                    product = next((p for p in products if p.product_code == product_code), None)
                                    if product:
                                        logger.info(f"Product found: {product.product_name}")
                                        # Calculate pricing with discounts and schemes
                                        pricing_info = db_service.get_product_pricing(product.id, quantity)
                                        order_items.append({
                                            'product_name': product.product_name,
                                            'product_code': product.product_code,
                                            'quantity': quantity,
                                            'unit_price': pricing_info['base_price'],
                                            'final_price': pricing_info['final_price'],
                                            'discount_percentage': pricing_info['discount_percentage'],
                                            'scheme_name': pricing_info['scheme_name'],
                                            'item_total': pricing_info['total_amount']
                                        })
                                        total_amount += pricing_info['total_amount']
                                        logger.info(f"Added {product_name} to order: {quantity} units, ${pricing_info['total_amount']}")
                                    else:
                                        logger.warning(f"Product not found in warehouse: {product_code}")
                                    break
                                else:
                                    logger.debug(f"No match for pattern {i+1}: {pattern}")
                        
                        logger.info(f"Total order items parsed: {len(order_items)}")
                        logger.info(f"Total amount: ${total_amount}")
                        
                        # If no items were parsed with regex, try LLM parsing as fallback
                        if not order_items:
                            logger.info("No items parsed with regex, trying LLM parsing...")
                            try:
                                # Use LLM classification service to parse order details
                                order_data = classification_service.parse_order_details(user_message, products)
                                logger.info(f"LLM parsing result: {order_data}")
                                
                                if order_data.get('order_ready', False) and order_data.get('cart_items'):
                                    for cart_item in order_data['cart_items']:
                                        product_code = cart_item['product_code']
                                        quantity = cart_item['quantity']
                                        
                                        # Get product details
                                        product = next((p for p in products if p.product_code == product_code), None)
                                        if product:
                                            # Calculate pricing with discounts and schemes
                                            pricing_info = db_service.get_product_pricing(product.id, quantity)
                                            order_items.append({
                                                'product_name': product.product_name,
                                                'product_code': product.product_code,
                                                'quantity': quantity,
                                                'unit_price': pricing_info['base_price'],
                                                'final_price': pricing_info['final_price'],
                                                'discount_percentage': pricing_info['discount_percentage'],
                                                'scheme_name': pricing_info['scheme_name'],
                                                'item_total': pricing_info['total_amount']
                                            })
                                            total_amount += pricing_info['total_amount']
                                            logger.info(f"LLM parsed {product.product_name}: {quantity} units")
                                
                                logger.info(f"LLM parsing result - items: {len(order_items)}, total: ${total_amount}")
                            except Exception as e:
                                logger.error(f"LLM parsing failed: {str(e)}")
                        
                        if order_items:
                            # Check if we should add to existing cart or create new
                            if has_order_session:
                                # Add to existing cart
                                existing_items = order_session.get('items', [])
                                for new_item in order_items:
                                    # Check if item already exists in cart
                                    existing_item = next((item for item in existing_items if item['product_code'] == new_item['product_code']), None)
                                    if existing_item:
                                        # Update quantity
                                        existing_item['quantity'] += new_item['quantity']
                                        existing_item['item_total'] += new_item['item_total']
                                    else:
                                        # Add new item
                                        existing_items.append(new_item)
                                
                                order_session['items'] = existing_items
                                order_session['total_cost'] = sum(item['item_total'] for item in existing_items)
                                order_session['final_total'] = order_session['total_cost']
                                order_session['status'] = 'confirming'
                                session['order_session'] = order_session
                                
                                # Create response showing updated cart
                                bot_response = f"""✅ **Products Added to Cart!**

**📋 Updated Cart Summary:**

"""
                                
                                for item in order_session['items']:
                                    bot_response += f"""**{item['product_name']} (QB{item['product_code'][2:]})**
   • Quantity: {item['quantity']} units
   • Base Price: ${item['unit_price']:,.2f} each
   • Discount: {item['discount_percentage']:.1f}% off
   • Final Price: ${item['final_price']:,.2f} each
   • Scheme: {item['scheme_name']}
   • Item Total: ${item['item_total']:,.2f}

"""
                                
                                bot_response += f"""**💰 Total Order Amount: ${order_session['final_total']:,.2f}**

**Next Steps:**
• Type 'add [product name]' to include more items
• Type 'place order' to finalize your selection
• Type 'remove [product name]' to remove items

Would you like to add more products or proceed with your order?"""
                                
                            else:
                                # Create new cart
                                order_session['status'] = 'confirming'
                                order_session['items'] = order_items
                                order_session['total_cost'] = total_amount
                                order_session['final_total'] = total_amount
                                session['order_session'] = order_session
                                
                                # Create response showing new cart
                                bot_response = f"""✅ **Order Received!**

Thank you for your order! I've processed your request and here are the details:

**📋 Order Summary:**

"""
                                
                                for item in order_items:
                                    bot_response += f"""**{item['product_name']} (QB{item['product_code'][2:]})**
   • Quantity: {item['quantity']} units
   • Base Price: ${item['unit_price']:,.2f} each
   • Discount: {item['discount_percentage']:.1f}% off
   • Final Price: ${item['final_price']:,.2f} each
   • Scheme: {item['scheme_name']}
   • Item Total: ${item['item_total']:,.2f}

"""
                                
                                bot_response += f"""**💰 Total Order Amount: ${total_amount:,.2f}**

**Next Steps:**
• Type 'add [product name]' to include more items
• Type 'place order' to finalize your selection
• Type 'remove [product name]' to remove items

Would you like to add more products or proceed with your order?"""
                            
                            return jsonify({
                                'response': bot_response,
                                'intent': 'PLACE_ORDER',
                                'confidence': 0.9
                            }), 200
                        else:
                            # No products found, ask for clarification
                            return jsonify({
                                'response': """I don't have the order details. Could you please specify which products and quantities you'd like to order?

Please use one of these formats:
• 'Quantum Processor - 3 units'
• '3 Quantum Processor'
• 'add 3 Quantum Processor'

**Available Products:**
• Quantum Processor (QB001)
• Neural Network Module (QB002)
• AI Memory Card (QB003)
• Quantum Sensors (QB004)
• AI Controller (QB005)""",
                                'intent': 'PLACE_ORDER',
                                'confidence': 0.5
                            }), 200
                            
                    except Exception as e:
                        logger.error(f"Error processing product listing: {str(e)}")
                        return jsonify({
                            'response': "I apologize, but I couldn't process your order. Please try again with a clear product list.",
                            'intent': 'PLACE_ORDER',
                            'confidence': 0.3
                        }), 200
                
                if is_detailed_confirmation:
                    # Enhanced order confirmation flow
                    try:
                        # Parse order details from user message
                        import re
                        
                        # Extract products and quantities from the user message
                        order_items = []
                        total_amount = 0
                        
                        # Define product mappings
                        product_mappings = {
                            'QB001': 'Quantum Processor',
                            'QB002': 'Neural Network Module', 
                            'QB003': 'AI Memory Card',
                            'QB004': 'Quantum Sensors',
                            'QB005': 'AI Controller'
                        }
                        
                        # Parse the detailed order confirmation message
                        # Look for product sections with detailed pricing
                        product_sections = re.findall(r'([A-Za-z\s]+)\(([A-Z0-9]+)\):.*?Quantity:\s*(\d+).*?Item Total:\s*\$([0-9,]+\.?\d*)', user_message, re.DOTALL)
                        
                        for product_name, product_code, quantity_str, item_total_str in product_sections:
                            quantity = int(quantity_str)
                            item_total = float(item_total_str.replace(',', ''))
                            
                            # Get product details
                            product = next((p for p in products if p.product_code == product_code), None)
                            if product:
                                # Calculate pricing with discounts and schemes
                                pricing_info = db_service.get_product_pricing(product.id, quantity)
                                order_items.append({
                                    'product_name': product.product_name,
                                    'product_code': product.product_code,
                                    'quantity': quantity,
                                    'unit_price': pricing_info['base_price'],
                                    'final_price': pricing_info['final_price'],
                                    'discount_percentage': pricing_info['discount_percentage'],
                                    'scheme_name': pricing_info['scheme_name'],
                                    'item_total': pricing_info['total_amount']
                                })
                                total_amount += pricing_info['total_amount']
                        
                        # If no products found with detailed parsing, try simple patterns
                        if not order_items:
                            for product_code, product_name in product_mappings.items():
                                # Try different patterns to find quantity
                                patterns = [
                                    rf'{product_name}.*?(\d+).*?units?',
                                    rf'(\d+).*?{product_name}',
                                    rf'{product_code}.*?(\d+)',
                                    rf'(\d+).*?{product_code}'
                                ]
                                
                                for pattern in patterns:
                                    match = re.search(pattern, user_message, re.IGNORECASE)
                                    if match:
                                        quantity = int(match.group(1))
                                        # Get product details
                                        product = next((p for p in products if p.product_code == product_code), None)
                                        if product:
                                            # Calculate pricing with discounts and schemes
                                            pricing_info = db_service.get_product_pricing(product.id, quantity)
                                            order_items.append({
                                                'product_name': product.product_name,
                                                'product_code': product.product_code,
                                                'quantity': quantity,
                                                'unit_price': pricing_info['base_price'],
                                                'final_price': pricing_info['final_price'],
                                                'discount_percentage': pricing_info['discount_percentage'],
                                                'scheme_name': pricing_info['scheme_name'],
                                                'item_total': pricing_info['total_amount']
                                            })
                                            total_amount += pricing_info['total_amount']
                                        break
                        
                        # Create clean user message format - this will be displayed as user message
                        user_order_summary = ""
                        for item in order_items:
                            user_order_summary += f"📦 {item['product_name']} - {item['quantity']} units\n"
                        
                        # Update order session with parsed data
                        order_session['status'] = 'confirming'
                        order_session['items'] = order_items
                        order_session['total_cost'] = total_amount
                        order_session['final_total'] = total_amount
                        session['order_session'] = order_session
                        
                        # Update order session to allow adding more items
                        order_session['status'] = 'confirming'
                        order_session['pending_confirmation'] = True
                        session['order_session'] = order_session
                        
                        # Create professional bot response with calculations
                        bot_response = f"""✅ **Order Confirmation Received**

Thank you for your order! I've processed your request and here are the details:

**📋 Order Summary:**

"""
                        
                        for item in order_items:
                            bot_response += f"""**{item['product_name']} (QB{item['product_code'][2:]})**
   • Quantity: {item['quantity']} units
   • Base Price: ${item['unit_price']:,.2f} each
   • Discount: {item['discount_percentage']:.1f}% off
   • Final Price: ${item['final_price']:,.2f} each
   • Scheme: {item['scheme_name']}
   • Item Total: ${item['item_total']:,.2f}

"""
                        
                        bot_response += f"""**💰 Total Order Amount: ${total_amount:,.2f}**

**🎯 Recommended Add-ons:**

1. **Quantum Sensors (QB004)** - $1,800.00
   - Perfect companion for Quantum Processors
   - Scheme: Buy 1 Get 15% Off

2. **Neural Network Module (QB002)** - $1,200.00  
   - Enhances AI Controller performance
   - Scheme: Buy 1 Get 20% Off

3. **AI Memory Card (QB003)** - $800.00
   - Additional storage for your AI systems
   - Scheme: Buy 3 Get 2 Free

**📝 Next Steps:**
• Type 'add [product name]' to include additional items
• Type 'place order' to finalize your current selection
• Type 'remove [product name]' to remove items from your order"""
                        
                        # Store the clean user message for display
                        session['clean_user_message'] = user_order_summary.strip()
                        
                        response = bot_response
                        
                    except Exception as e:
                        logger.error(f"Error parsing order details: {str(e)}")
                        response = f"**Order Summary:**\n{user_message}\n\nI've received your order confirmation. Would you like to proceed with placing this order?"
                    
                elif is_finalizing and has_order_session:
                    # Use order session data to create order
                    order_session['status'] = 'confirming'
                    session['order_session'] = order_session
                    
                    # Convert order session items to cart format
                    cart_items = []
                    for item in order_session['items']:
                        cart_items.append({
                            'product_code': item['product_code'],
                            'quantity': item['quantity']
                        })
                    
                    # Create the order
                    order, message = order_service.create_order_from_cart(
                        user_id=session_user_id,
                        cart_items=cart_items,
                        warehouse_id=warehouse.id,
                        warehouse_location=warehouse_location,
                        user_email=user.email
                    )
                    
                    if order:
                        # Update order session to completed
                        order_session['status'] = 'completed'
                        order_session['order_id'] = order.order_id
                        session['order_session'] = order_session
                        
                        response = f"""🎉 Order Placed Successfully!

Order ID: {order.order_id}
Total Amount: ${order.total_amount:.2f}
Status: {order.status.title()}

Your order has been confirmed and a confirmation email has been sent to {user.email}. You can track your order using the Order ID: {order.order_id}

Thank you for choosing Quantum Blue!"""
                    else:
                        response = f"❌ Order failed: {message}"
                        
                elif is_finalizing and not has_order_session:
                    # User wants to finalize but no order session data - try to parse from conversation
                    session_id = session.get('session_id')
                    conversation_history = []
                    if session_id:
                        chat_session = ChatSession.query.filter_by(session_id=session_id).first()
                        if chat_session:
                            conversations = db_service.get_session_conversations(session_id)
                            conversation_history = [conv.to_dict() for conv in conversations[-10:]]  # Last 10 conversations
                    
                    # Parse order details and create order
                    order_data = classification_service.parse_order_details(user_message, products, conversation_history)
                    
                    if order_data.get('order_ready') and order_data.get('cart_items'):
                        # Create the order
                        order, message = order_service.create_order_from_cart(
                            user_id=session_user_id,
                            cart_items=order_data['cart_items'],
                            warehouse_id=warehouse.id,
                            warehouse_location=warehouse_location,
                            user_email=user.email
                        )
                        
                        if order:
                            # Update order session to completed
                            order_session['status'] = 'completed'
                            order_session['order_id'] = order.order_id
                            session['order_session'] = order_session
                            
                            response = f"""🎉 Order Placed Successfully!

Order ID: {order.order_id}
Total Amount: ${order.total_amount:.2f}
Status: {order.status.title()}

Your order has been confirmed and a confirmation email has been sent to {user.email}. You can track your order using the Order ID: {order.order_id}

Thank you for choosing Quantum Blue!"""
                        else:
                            response = f"❌ Order failed: {message}"
                    else:
                        # User wants to place order but details are unclear
                        response = "I don't have the order details. Could you please specify which products and quantities you'd like to order?"
                else:
                    # User is browsing or asking about products
                    order_session['status'] = 'browsing'
                    session['order_session'] = order_session
                    
                    # Load products for browsing
                    products = []
                    if warehouse:
                        products = db_service.get_products_by_warehouse(warehouse.id)
                    
                    # Generate response with interactive options
                    response = classification_service.generate_order_flow_response(
                        user_message, products, warehouse_location
                    )
                    
                    # Add interactive product options
                    if products:
                        response += "\n\n🛒 **Quick Product Selection:**\n"
                        for i, product in enumerate(products[:5], 1):
                            response += f"{i}. {product.product_name} (QB{product.product_code[2:]}) - ${product.price_of_product:,.2f} - Available: {product.available_for_sale}\n"
                        response += "\n**Quick Actions:**\n"
                        response += "• Type product name + quantity (e.g., '100 quantum processor')\n"
                        response += "• Ask for cost calculation\n"
                        response += "• Say 'show all products' for complete list"
            else:
                response = "I couldn't find your warehouse. Please contact support."
            
        elif intent == 'TRACK_ORDER':
            # Get user's orders
            orders = db_service.get_orders_by_email(user.email)
            
            # Check if user is asking for specific order details
            order_id_patterns = ['QB', 'order', 'track']
            has_order_id = any(pattern in user_message.upper() for pattern in order_id_patterns)
            
            if has_order_id and orders:
                # User mentioned specific order - try to find it
                tracking_session['status'] = 'selecting'
                try:
                    tracking_session['available_orders'] = [order.to_dict() for order in orders]
                except AttributeError as e:
                    logger.error(f"Error calling to_dict on Order object: {e}")
                    logger.error(f"Order object type: {type(orders[0]) if orders else 'No orders'}")
                    logger.error(f"Order object attributes: {dir(orders[0]) if orders else 'No orders'}")
                    # Fallback: create dict manually
                    tracking_session['available_orders'] = []
                    for order in orders:
                        tracking_session['available_orders'].append({
                            'id': order.id,
                            'order_id': order.order_id,
                            'user_email': order.user_email,
                            'warehouse_location': order.warehouse_location,
                            'total_amount': order.total_amount,
                            'status': order.status,
                            'order_date': order.order_date.isoformat(),
                            'updated_at': order.updated_at.isoformat()
                        })
                session['tracking_session'] = tracking_session
                
                # Look for order ID in the message
                import re
                order_id_match = re.search(r'QB[A-Z0-9]+', user_message.upper())
                if order_id_match:
                    order_id = order_id_match.group()
                    # Find the specific order
                    specific_order = next((order for order in orders if order.order_id == order_id), None)
                    if specific_order:
                        tracking_session['status'] = 'viewing'
                        tracking_session['selected_order_id'] = order_id
                        try:
                            tracking_session['order_details'] = specific_order.to_dict()
                        except AttributeError as e:
                            logger.error(f"Error calling to_dict on specific Order object: {e}")
                            # Fallback: create dict manually
                            tracking_session['order_details'] = {
                                'id': specific_order.id,
                                'order_id': specific_order.order_id,
                                'user_email': specific_order.user_email,
                                'warehouse_location': specific_order.warehouse_location,
                                'total_amount': specific_order.total_amount,
                                'status': specific_order.status,
                                'order_date': specific_order.order_date.isoformat(),
                                'updated_at': specific_order.updated_at.isoformat()
                            }
                        session['tracking_session'] = tracking_session
                        
                        # Get detailed order information
                        order_details, message = order_service.get_order_status(order_id)
                        if order_details:
                            items_text = ""
                            for item in order_details['items']:
                                items_text += f"• {item['product_name']} (QB{item['product_code'][2:]}) - {item['quantity']} units × ${item['unit_price']:,.2f} = ${item['total_price']:,.2f}\n"
                            
                            response = f"""📦 Order Details for {order_id}:

Status: {order_details['status'].title()}
Order Date: {order_details['order_date'][:10]}
Warehouse: {order_details['warehouse_location']}

Items:
{items_text}
Total Amount: ${order_details['total_amount']:,.2f}

Would you like to track another order or need more information?"""
                        else:
                            response = f"Order {order_id} not found. Here are your available orders:"
                            for order in orders[:5]:
                                response += f"\n• {order.order_id} - {order.status} (${order.total_amount:,.2f})"
                    else:
                        response = f"Order {order_id} not found. Here are your available orders:"
                        for order in orders[:5]:
                            response += f"\n• {order.order_id} - {order.status} (${order.total_amount:,.2f})"
                else:
                    # Show available orders for selection
                    response = "Here are your recent orders. Please select one to track:\n\n"
                    for i, order in enumerate(orders[:5], 1):
                        response += f"{i}. Order {order.order_id} - {order.status} (${order.total_amount:,.2f}) - {order.order_date.strftime('%Y-%m-%d')}\n"
                    response += "\nPlease specify the order ID or number to track."
            else:
                # General tracking request - show available orders
                tracking_session['status'] = 'selecting'
                try:
                    tracking_session['available_orders'] = [order.to_dict() for order in orders]
                except AttributeError as e:
                    logger.error(f"Error calling to_dict on Order objects: {e}")
                    # Fallback: create dict manually
                    tracking_session['available_orders'] = []
                    for order in orders:
                        tracking_session['available_orders'].append({
                            'id': order.id,
                            'order_id': order.order_id,
                            'user_email': order.user_email,
                            'warehouse_location': order.warehouse_location,
                            'total_amount': order.total_amount,
                            'status': order.status,
                            'order_date': order.order_date.isoformat(),
                            'updated_at': order.updated_at.isoformat()
                        })
                session['tracking_session'] = tracking_session
                
                if orders:
                    response = "Here are your recent orders. Please select one to track:\n\n"
                    for i, order in enumerate(orders[:5], 1):
                        response += f"{i}. Order {order.order_id} - {order.status} (${order.total_amount:,.2f}) - {order.order_date.strftime('%Y-%m-%d')}\n"
                    response += "\nPlease specify the order ID or number to track."
                else:
                    response = "You don't have any orders yet. Would you like to place a new order?"
            
        elif intent == 'COMPANY_INFO':
            # Use web search for real-time company information
            search_result = web_search_service.search_with_synthesis(user_message, user_message)
            if search_result.get('synthesized_response'):
                response = search_result.get('synthesized_response')
            else:
                # Fallback to database company info
                company_info = db_service.get_company_info()
                response = f"""Welcome to {company_info['company_name']}!

{company_info['description']}

Our features:
{chr(10).join([f"• {feature}" for feature in company_info['features']])}

Contact us:
• Email: {company_info['contact_info']['email']}
• Phone: {company_info['contact_info']['phone']}
• Address: {company_info['contact_info']['address']}

How can I help you today?"""
            
        elif intent == 'WEB_SEARCH':
            # Perform web search
            search_result = web_search_service.search_with_synthesis(user_message, user_message)
            response = search_result.get('synthesized_response', 'I couldn\'t find sufficient information to answer your query.')
            
        else:
            # General conversation with professional tone
            response = llm_service.generate_response(
                user_message,
                conversation_history=[],
                context_data=context_data
            ).get('response', """Hello! I'm your Quantum Blue assistant, and I'm here to help you with:

**🛒 Order Management:**
• Place new orders
• Track existing orders
• Calculate costs and discounts

**📦 Product Information:**
• Browse our product catalog
• Get pricing and availability
• Learn about special offers

**🏢 Company Services:**
• Learn about Quantum Blue
• Get support and assistance

How can I assist you today?""")

        # 3. Save conversation
        session_id = session.get('session_id')
        if session_id:
            chat_session = ChatSession.query.filter_by(session_id=session_id).first()
            if chat_session:
                db_service.save_conversation(
                    user_id=session_user_id,
                    session_id=session_id,
                    user_message=user_message,
                    bot_response=response,
                    data_sources=[intent],
                    response_time=0.5
                )

        # Get clean user message if available
        clean_user_message = session.get('clean_user_message', user_message)
        
        return jsonify({
            'response': response,
            'intent': intent,
            'confidence': classification_result.get('confidence', 0.0),
            'user_message': clean_user_message
        }), 200
    
    except Exception as e:
        logger.error(f'Error processing message: {str(e)}')
        try:
            db.session.rollback()
        except:
            pass
        return jsonify({'error': 'Failed to process message'}), 500

# --- Helper Routes (DB and Session Handling Fixed) ---

@chatbot_bp.route('/history')
def get_history():
    """Get conversation history"""
    session_user_id = session.get('user_id')
    if not session_user_id:
        return jsonify({'conversations': []})
    conversations = Conversation.query.filter_by(
        user_id=session_user_id
    ).order_by(Conversation.created_at.desc()).limit(50).all()
    
    return jsonify({
        'conversations': [conv.to_dict() for conv in conversations]
    })

@chatbot_bp.route('/export', methods=['POST'])
def export_conversation():
    """Export and email conversation"""
    session_user_id = session.get('user_id')
    if not session_user_id:
        return jsonify({'error': 'No verified user session'}), 400
    
    try:
        conversations = Conversation.query.filter_by(
            user_id=session_user_id
        ).order_by(Conversation.created_at.asc()).all()
        
        if not conversations:
            return jsonify({'error': 'No conversations to export'}), 400
        
        from app.models import User
        user = User.query.get(session_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 400
        
        conversation_data = {
            'user_name': user.name,
            'date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'conversations': [conv.to_dict() for conv in conversations]
        }
        
        admin_email = current_app.config['ADMIN_EMAIL']
        send_conversation_email(
            user.email,
            admin_email,
            conversation_data
        )
        
        return jsonify({'message': 'Conversation exported and emailed successfully'}), 200
    
    except Exception as e:
        logger.error(f'Export error: {str(e)}')
        return jsonify({'error': 'Failed to export conversation'}), 500

@chatbot_bp.route('/order-status', methods=['GET'])
def get_order_status():
    """Get current order and tracking session status"""
    session_user_id = session.get('user_id')
    if not session_user_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    order_session = session.get('order_session', reset_order_session())
    tracking_session = session.get('tracking_session', reset_tracking_session())
    return jsonify({
        'order_session': order_session,
        'tracking_session': tracking_session,
        'user_id': session_user_id
    }), 200

@chatbot_bp.route('/clear', methods=['POST'])
def clear_conversation():
    """Export conversation via email, then delete all history and reset onboarding"""
    session_user_id = session.get('user_id')
    session_id = session.get('session_id')
    
    # 1. Handle case where user is not logged in/verified. This is a clean exit path.
    if not session_user_id:
        logger.warning('Clear operation attempted without user_id in session. Resetting session keys.')
        for key in ['onboarding_state', 'onboarding', 'user_id', 'session_id', 'warehouse_location']:
            session.pop(key, None)
        return jsonify({'message': 'No conversation to clear, session reset.'}), 200
    
    try:
        # 2. Retrieve data
        user = User.query.get(session_user_id)
        conversations = []
        db_service = get_db_service()  # Initialize db_service at the beginning
        
        if session_id:
            chat_session = ChatSession.query.filter_by(session_id=session_id).first()
            if chat_session:
                conversations = db_service.get_session_conversations(session_id)
        else:
            conversations = Conversation.query.filter_by(user_id=session_user_id).order_by(Conversation.created_at.asc()).all()
        
        # 3. Export Email logic (Only run if user and conversations exist)
        if user and conversations:
            conversation_data = {
                'user_name': user.name,
                'date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'conversations': [conv.to_dict() for conv in conversations]
            }
            admin_email = current_app.config['ADMIN_EMAIL']
            
            try:
                # Attempt to send email
                send_conversation_email(user.email, admin_email, conversation_data)
                logger.info(f"Conversation exported via email for user {session_user_id}.")
            except Exception as email_e:
                # Log email failure but proceed with database cleanup
                logger.error(f"Email export failed for user {session_user_id}: {str(email_e)}. Proceeding with delete.")

        # 4. Delete conversations and deactivate session
        try:
            # Ensure we have a clean transaction state
            db.session.rollback()
            
            if session_id:
                success = db_service.delete_session_conversations(session_id)
                if not success:
                    logger.warning(f"Failed to delete session conversations for {session_id}")
                db_service.deactivate_session(session_id)
            else:
                Conversation.query.filter_by(user_id=session_user_id).delete()
                db.session.commit()
            
            logger.info(f"Successfully cleared conversations for user {session_user_id}")
        except Exception as db_e:
            logger.error(f"Database cleanup failed for user {session_user_id}: {str(db_e)}")
            try:
                db.session.rollback()
            except:
                pass
            raise db_e
        
        # 5. Reset session
        for key in ['onboarding_state', 'onboarding', 'user_id', 'session_id', 'warehouse_location', 'order_session', 'tracking_session']:
            session.pop(key, None)
            
        return jsonify({'message': 'Conversation exported and cleared'}), 200 # Success path
        
    except Exception as e:
        logger.error(f'Clear error (DB operation failed) for user {session_user_id}: {str(e)}')
        db.session.rollback() 
        
        # Failure path must return a response object
        return jsonify({'error': 'Failed to clear conversation. Database operation failed.'}), 500

# --- New Order Management Routes ---

@chatbot_bp.route('/orders', methods=['GET'])
def get_user_orders():
    """Get user's orders"""
    session_user_id = session.get('user_id')
    if not session_user_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    try:
        order_service = get_order_service()
        orders, message = order_service.get_user_orders(session_user_id)
        return jsonify({'orders': orders, 'message': message}), 200
    except Exception as e:
        logger.error(f'Error getting orders: {str(e)}')
        return jsonify({'error': 'Failed to get orders'}), 500

@chatbot_bp.route('/orders/<order_id>', methods=['GET'])
def get_order_details(order_id):
    """Get specific order details"""
    session_user_id = session.get('user_id')
    if not session_user_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    try:
        order_service = get_order_service()
        order_details, message = order_service.get_order_status(order_id)
        if order_details:
            return jsonify({'order': order_details, 'message': message}), 200
        else:
            return jsonify({'error': message}), 404
    except Exception as e:
        logger.error(f'Error getting order details: {str(e)}')
        return jsonify({'error': 'Failed to get order details'}), 500

@chatbot_bp.route('/products', methods=['GET'])
def get_products():
    """Get products for user's warehouse"""
    session_user_id = session.get('user_id')
    warehouse_location = session.get('warehouse_location')
    
    if not session_user_id or not warehouse_location:
        return jsonify({'error': 'User not authenticated or warehouse not set'}), 401
    
    try:
        db_service = get_db_service()
        warehouse = db_service.get_warehouse_by_location(warehouse_location)
        if warehouse:
            products = db_service.get_products_by_warehouse(warehouse.id)
            product_list = []
            for product in products:
                product_list.append({
                    'id': product.id,
                    'product_code': product.product_code,
                    'product_name': product.product_name,
                    'product_description': product.product_description,
                    'price': product.price_of_product,
                    'available_quantity': product.available_for_sale,
                    'discount': product.discount,
                    'scheme': product.scheme
                })
            return jsonify({'products': product_list}), 200
        else:
            return jsonify({'error': 'Warehouse not found'}), 404
    except Exception as e:
        logger.error(f'Error getting products: {str(e)}')
        return jsonify({'error': 'Failed to get products'}), 500

@chatbot_bp.route('/place-order', methods=['POST'])
def place_order():
    """Place an order"""
    session_user_id = session.get('user_id')
    warehouse_location = session.get('warehouse_location')
    
    if not session_user_id or not warehouse_location:
        return jsonify({'error': 'User not authenticated or warehouse not set'}), 401
    
    try:
        data = request.get_json()
        cart_items = data.get('cart_items', [])
        
        if not cart_items:
            return jsonify({'error': 'No items in cart'}), 400
        
        # Get user and warehouse
        user = User.query.get(session_user_id)
        db_service = get_db_service()
        warehouse = db_service.get_warehouse_by_location(warehouse_location)
        
        if not warehouse:
            return jsonify({'error': 'Warehouse not found'}), 404
        
        # Create order
        order_service = get_order_service()
        order, message = order_service.create_order_from_cart(
            user_id=session_user_id,
            cart_items=cart_items,
            warehouse_id=warehouse.id,
            warehouse_location=warehouse_location,
            user_email=user.email
        )
        
        if order:
            return jsonify({
                'order_id': order.order_id,
                'message': message,
                'total_amount': order.total_amount
            }), 200
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        logger.error(f'Error placing order: {str(e)}')
        return jsonify({'error': 'Failed to place order'}), 500

@chatbot_bp.route('/api/products', methods=['GET'])
def get_all_products():
    """Get products for user's warehouse with real-time quantities"""
    session_user_id = session.get('user_id')
    warehouse_location = session.get('warehouse_location')
    
    if not session_user_id or not warehouse_location:
        return jsonify({'error': 'User not authenticated or warehouse not set'}), 401
    
    try:
        db_service = get_db_service()
        warehouse = db_service.get_warehouse_by_location(warehouse_location)
        if warehouse:
            products = db_service.get_products_by_warehouse(warehouse.id)
            
            # Convert to API format
            product_list = []
            for product in products:
                product_list.append({
                    'product_code': product.product_code,
                    'product_name': product.product_name,
                    'product_description': product.product_description,
                    'price_of_product': float(product.price_of_product),
                    'available_for_sale': int(product.available_for_sale),
                    'discount': float(product.discount) if product.discount else 0,
                    'scheme': product.scheme,
                    'batch_number': product.batch_number,
                    'expiry_date': product.expiry_date.isoformat() if product.expiry_date else None
                })
            
            return jsonify({
                'products': product_list,
                'warehouse_location': warehouse_location,
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({'error': 'Warehouse not found'}), 404
        
    except Exception as e:
        logger.error(f'Error getting products: {str(e)}')
        return jsonify({'error': 'Failed to get products'}), 500

@chatbot_bp.route('/api/pricing', methods=['POST'])
def get_pricing():
    """Get dynamic pricing for products with discounts and schemes"""
    try:
        data = request.get_json()
        product_codes = data.get('product_codes', [])
        quantities = data.get('quantities', [])
        
        if not product_codes:
            return jsonify({'error': 'No product codes provided'}), 400
        
        db_service = get_db_service()
        pricing_data = []
        
        for i, product_code in enumerate(product_codes):
            quantity = quantities[i] if i < len(quantities) else 1
            
            # Get product from database
            product = db_service.get_product_by_code(product_code)
            if not product:
                # Fallback pricing if product not found
                pricing_data.append({
                    'product_code': product_code,
                    'base_price': 0,
                    'final_price': 0,
                    'discount_percentage': 0,
                    'discount_amount': 0,
                    'scheme_name': None,
                    'total_amount': 0,
                    'total_quantity': quantity,
                    'paid_quantity': quantity,
                    'free_quantity': 0
                })
                continue
            
            # Get pricing with discounts and schemes
            pricing_info = db_service.get_product_pricing(product.id, quantity)
            logger.info(f"Pricing for {product_code} (qty {quantity}): {pricing_info}")
            
            pricing_data.append({
                'product_code': product_code,
                'base_price': pricing_info['base_price'],
                'final_price': pricing_info['final_price'],
                'discount_percentage': pricing_info['discount_percentage'],
                'discount_amount': pricing_info['discount_amount'],
                'scheme_name': pricing_info['scheme_name'],
                'total_amount': pricing_info['total_amount'],
                'total_quantity': pricing_info['total_quantity'],
                'paid_quantity': pricing_info['paid_quantity'],
                'free_quantity': pricing_info['free_quantity']
            })
        
        return jsonify({
            'pricing': pricing_data,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f'Error getting pricing: {str(e)}')
        return jsonify({'error': 'Failed to get pricing'}), 500

@chatbot_bp.route('/api/update-quantities', methods=['POST'])
def update_quantities():
    """Update product quantities after order selection"""
    try:
        data = request.get_json()
        product_quantities = data.get('product_quantities', {})
        
        if not product_quantities:
            return jsonify({'error': 'No product quantities provided'}), 400
        
        db_service = get_db_service()
        success = db_service.update_product_quantities(product_quantities)
        
        if success:
            return jsonify({
                'message': 'Product quantities updated successfully',
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({'error': 'Failed to update quantities'}), 500
        
    except Exception as e:
        logger.error(f'Error updating quantities: {str(e)}')
        return jsonify({'error': 'Failed to update quantities'}), 500

# Enhanced Cart Management API Endpoints

@chatbot_bp.route('/api/cart/init', methods=['POST'])
def init_cart():
    """Initialize a new cart session"""
    session_user_id = session.get('user_id')
    warehouse_location = session.get('warehouse_location')
    
    if not session_user_id or not warehouse_location:
        return jsonify({'error': 'User not authenticated or warehouse not set'}), 401
    
    try:
        db_service = get_db_service()
        warehouse = db_service.get_warehouse_by_location(warehouse_location)
        
        if not warehouse:
            return jsonify({'error': 'Warehouse not found'}), 404
        
        enhanced_order_service = get_enhanced_order_service()
        cart_id, message = enhanced_order_service.initialize_cart_session(session_user_id, warehouse.id)
        
        if cart_id:
            return jsonify({
                'cart_id': cart_id,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        logger.error(f'Error initializing cart: {str(e)}')
        return jsonify({'error': 'Failed to initialize cart'}), 500

@chatbot_bp.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    """Add item to cart"""
    session_user_id = session.get('user_id')
    warehouse_location = session.get('warehouse_location')
    
    if not session_user_id or not warehouse_location:
        return jsonify({'error': 'User not authenticated or warehouse not set'}), 401
    
    try:
        data = request.get_json()
        product_code = data.get('product_code')
        quantity = data.get('quantity', 1)
        
        if not product_code:
            return jsonify({'error': 'Product code is required'}), 400
        
        db_service = get_db_service()
        warehouse = db_service.get_warehouse_by_location(warehouse_location)
        
        if not warehouse:
            return jsonify({'error': 'Warehouse not found'}), 404
        
        enhanced_order_service = get_enhanced_order_service()
        success, message = enhanced_order_service.add_item_to_cart(
            product_code, quantity, session_user_id, warehouse.id
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        logger.error(f'Error adding to cart: {str(e)}')
        return jsonify({'error': 'Failed to add item to cart'}), 500

@chatbot_bp.route('/api/cart/remove', methods=['POST'])
def remove_from_cart():
    """Remove item from cart"""
    try:
        data = request.get_json()
        product_code = data.get('product_code')
        
        if not product_code:
            return jsonify({'error': 'Product code is required'}), 400
        
        enhanced_order_service = get_enhanced_order_service()
        success, message = enhanced_order_service.remove_item_from_cart(product_code)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        logger.error(f'Error removing from cart: {str(e)}')
        return jsonify({'error': 'Failed to remove item from cart'}), 500

@chatbot_bp.route('/api/cart/update', methods=['POST'])
def update_cart_item():
    """Update item quantity in cart"""
    try:
        data = request.get_json()
        product_code = data.get('product_code')
        quantity = data.get('quantity')
        
        if not product_code or quantity is None:
            return jsonify({'error': 'Product code and quantity are required'}), 400
        
        enhanced_order_service = get_enhanced_order_service()
        success, message = enhanced_order_service.update_item_quantity(product_code, quantity)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        logger.error(f'Error updating cart item: {str(e)}')
        return jsonify({'error': 'Failed to update cart item'}), 500

@chatbot_bp.route('/api/cart/summary', methods=['GET'])
def get_cart_summary():
    """Get current cart summary"""
    try:
        enhanced_order_service = get_enhanced_order_service()
        cart_summary, message = enhanced_order_service.get_cart_summary()
        
        if cart_summary:
            return jsonify({
                'cart': cart_summary,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        logger.error(f'Error getting cart summary: {str(e)}')
        return jsonify({'error': 'Failed to get cart summary'}), 500

@chatbot_bp.route('/api/cart/confirm', methods=['POST'])
def confirm_cart():
    """Confirm cart and create order"""
    session_user_id = session.get('user_id')
    warehouse_location = session.get('warehouse_location')
    
    if not session_user_id or not warehouse_location:
        return jsonify({'error': 'User not authenticated or warehouse not set'}), 401
    
    try:
        db_service = get_db_service()
        warehouse = db_service.get_warehouse_by_location(warehouse_location)
        user = User.query.get(session_user_id)
        
        if not warehouse or not user:
            return jsonify({'error': 'Warehouse or user not found'}), 404
        
        enhanced_order_service = get_enhanced_order_service()
        order, message = enhanced_order_service.confirm_cart(
            session_user_id, warehouse.id, user.email
        )
        
        if order:
            return jsonify({
                'order_id': order.order_id,
                'total_amount': order.total_amount,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        logger.error(f'Error confirming cart: {str(e)}')
        return jsonify({'error': 'Failed to confirm cart'}), 500

@chatbot_bp.route('/api/cart/clear', methods=['POST'])
def clear_cart():
    """Clear current cart"""
    try:
        enhanced_order_service = get_enhanced_order_service()
        success, message = enhanced_order_service.clear_cart()
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        logger.error(f'Error clearing cart: {str(e)}')
        return jsonify({'error': 'Failed to clear cart'}), 500

@chatbot_bp.route('/api/update-cart', methods=['POST'])
def update_cart():
    """Update cart with selected products from frontend"""
    session_user_id = session.get('user_id')
    warehouse_location = session.get('warehouse_location')
    
    if not session_user_id or not warehouse_location:
        return jsonify({'error': 'User not authenticated or warehouse not set'}), 401
    
    try:
        data = request.get_json()
        selected_products = data.get('selected_products', [])
        action = data.get('action', 'update_cart')
        
        if not selected_products:
            return jsonify({'error': 'No products provided'}), 400
        
        # Get user and warehouse
        user = User.query.get(session_user_id)
        db_service = get_db_service()
        warehouse = db_service.get_warehouse_by_location(warehouse_location)
        
        if not warehouse or not user:
            return jsonify({'error': 'Warehouse or user not found'}), 404
        
        # Update order session with selected products - APPEND to existing cart
        order_session = session.get('order_session', {})
        if not order_session:
            order_session = {
                'status': 'idle',
                'items': [],
                'total_cost': 0,
                'discount_applied': 0,
                'final_total': 0,
                'order_id': None,
                'cart_id': None,
                'last_updated': datetime.utcnow().isoformat(),
                'user_selections': [],
                'pending_confirmation': False
            }
        
        order_session['status'] = 'confirming'
        
        # Get existing items to preserve them
        existing_items = order_session.get('items', [])
        existing_total = order_session.get('final_total', 0)
        
        # Process new selected products
        for product in selected_products:
            # Get product details from database
            db_product = db_service.get_product_by_code(product['code'])
            if db_product:
                # Calculate pricing with discounts and schemes
                pricing_info = db_service.get_product_pricing(db_product.id, product['quantity'])
                
                # Check if this product already exists in cart
                existing_item = next((item for item in existing_items if item['product_code'] == product['code']), None)
                
                if existing_item:
                    # Update existing item quantity and totals (REPLACE quantity, don't add)
                    old_quantity = existing_item['quantity']
                    existing_item['quantity'] = product['quantity']  # Replace quantity instead of adding
                    # Recalculate pricing for the new quantity
                    updated_pricing = db_service.get_product_pricing(db_product.id, existing_item['quantity'])
                    existing_item['final_price'] = updated_pricing['final_price']
                    existing_item['discount_percentage'] = updated_pricing['discount_percentage']
                    existing_item['scheme_name'] = updated_pricing['scheme_name']
                    existing_item['item_total'] = updated_pricing['total_amount']
                    
                    logger.info(f"Updated existing item {product['code']}: {old_quantity} -> {product['quantity']}")
                else:
                    # Add new item to cart
                    order_item = {
                        'product_name': db_product.product_name,
                        'product_code': db_product.product_code,
                        'quantity': product['quantity'],
                        'unit_price': pricing_info['base_price'],
                        'final_price': pricing_info['final_price'],
                        'discount_percentage': pricing_info['discount_percentage'],
                        'scheme_name': pricing_info['scheme_name'],
                        'item_total': pricing_info['total_amount']
                    }
                    existing_items.append(order_item)
        
        # Update cart totals
        order_session['items'] = existing_items
        order_session['total_cost'] = sum(item['item_total'] for item in existing_items)
        order_session['final_total'] = order_session['total_cost']
        order_session['last_updated'] = datetime.utcnow().isoformat()
        session['order_session'] = order_session
        
        # Force session to be saved
        session.modified = True
        
        # Debug logging
        logger.info(f"Cart updated - Items count: {len(existing_items)}")
        logger.info(f"Cart updated - Total amount: {order_session['final_total']}")
        for item in existing_items:
            logger.info(f"Updated cart item: {item['product_name']} - Qty: {item['quantity']} - Total: {item['item_total']}")
        
        return jsonify({
            'success': True,
            'message': 'Cart updated successfully',
            'cart_items': len(order_session['items']),
            'total_amount': order_session['final_total'],
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f'Error updating cart: {str(e)}')
        return jsonify({'error': 'Failed to update cart'}), 500

# NOTE: The helper function _needs_web_search is obsolete and should be removed.
# I assume this was removed in your latest deployment of this file.