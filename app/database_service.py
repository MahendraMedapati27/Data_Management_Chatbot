import logging
from datetime import datetime
from sqlalchemy import text, and_, or_
from app import db
from app.models import User, Warehouse, Product, Order, OrderItem, ChatSession, Conversation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for database operations"""
    
    def __init__(self):
        self.logger = logger
    
    # User Management
    def get_user_by_email(self, email):
        """Get user by email"""
        return User.query.filter_by(email=email).first()
    
    def create_user(self, name, email, phone, warehouse_location=None):
        """Create new user"""
        user = User(
            name=name,
            email=email,
            phone=phone,
            warehouse_location=warehouse_location
        )
        db.session.add(user)
        db.session.commit()
        return user
    
    def update_user_warehouse(self, user_id, warehouse_location):
        """Update user's warehouse location"""
        user = User.query.get(user_id)
        if user:
            user.warehouse_location = warehouse_location
            user.last_verification = datetime.utcnow()
            db.session.commit()
            return user
        return None
    
    # Warehouse Management
    def get_warehouses(self):
        """Get all active warehouses"""
        return Warehouse.query.filter_by(is_active=True).all()
    
    def get_warehouse_by_location(self, location_name):
        """Get warehouse by location name"""
        return Warehouse.query.filter_by(location_name=location_name, is_active=True).first()
    
    def create_warehouse(self, location_name, address=None, city=None, state=None, country=None):
        """Create new warehouse"""
        warehouse = Warehouse(
            location_name=location_name,
            address=address,
            city=city,
            state=state,
            country=country
        )
        db.session.add(warehouse)
        db.session.commit()
        return warehouse
    
    # Product Management
    def get_products_by_warehouse(self, warehouse_id):
        """Get products by warehouse"""
        return Product.query.filter_by(warehouse_id=warehouse_id).all()
    
    def get_products_by_warehouse_location(self, warehouse_location):
        """Get products by warehouse location name"""
        warehouse = self.get_warehouse_by_location(warehouse_location)
        if warehouse:
            return self.get_products_by_warehouse(warehouse.id)
        return []
    
    def get_product_by_code_and_warehouse(self, product_code, warehouse_id):
        """Get specific product by code and warehouse"""
        return Product.query.filter_by(
            product_code=product_code,
            warehouse_id=warehouse_id
        ).first()
    
    def update_product_quantities(self, product_id, quantity_ordered):
        """Update product quantities when order is placed"""
        product = Product.query.get(product_id)
        if product and product.available_for_sale >= quantity_ordered:
            product.blocked_quantity += quantity_ordered
            product.update_available_quantity()
            db.session.commit()
            return True
        return False
    
    def search_products(self, query, warehouse_id=None):
        """Search products by name or code"""
        search_filter = or_(
            Product.product_name.ilike(f'%{query}%'),
            Product.product_code.ilike(f'%{query}%'),
            Product.product_description.ilike(f'%{query}%')
        )
        
        if warehouse_id:
            return Product.query.filter(
                and_(search_filter, Product.warehouse_id == warehouse_id)
            ).all()
        else:
            return Product.query.filter(search_filter).all()
    
    # Order Management
    def create_order(self, user_id, warehouse_id, warehouse_location, user_email):
        """Create new order"""
        order = Order(
            user_id=user_id,
            warehouse_id=warehouse_id,
            warehouse_location=warehouse_location,
            user_email=user_email
        )
        order.generate_order_id()
        db.session.add(order)
        db.session.commit()
        return order
    
    def add_order_item(self, order_id, product_id, product_code, quantity, unit_price, total_price=None):
        """Add item to order"""
        if total_price is None:
            total_price = quantity * unit_price
        order_item = OrderItem(
            order_id=order_id,
            product_id=product_id,
            product_code=product_code,
            product_quantity_ordered=quantity,
            unit_price=unit_price,
            total_price=total_price
        )
        db.session.add(order_item)
        db.session.commit()
        return order_item
    
    def update_order_total(self, order_id):
        """Update order total amount"""
        order = Order.query.get(order_id)
        if order:
            total = sum(item.total_price for item in order.order_items)
            order.total_amount = total
            db.session.commit()
            return order
        return None
    
    def get_orders_by_user(self, user_id):
        """Get orders by user"""
        return Order.query.filter_by(user_id=user_id).order_by(Order.order_date.desc()).all()
    
    def get_orders_by_email(self, email):
        """Get orders by email"""
        return Order.query.filter_by(user_email=email).order_by(Order.order_date.desc()).all()
    
    def get_order_by_id(self, order_id):
        """Get order by order ID"""
        return Order.query.filter_by(order_id=order_id).first()
    
    def update_order_status(self, order_id, status):
        """Update order status"""
        order = Order.query.filter_by(order_id=order_id).first()
        if order:
            order.status = status
            db.session.commit()
            return order
        return None
    
    # Chat Session Management
    def create_chat_session(self, user_id):
        """Create new chat session"""
        session = ChatSession(user_id=user_id)
        session.generate_session_id()
        db.session.add(session)
        db.session.commit()
        return session
    
    def get_active_session(self, user_id):
        """Get active chat session for user"""
        return ChatSession.query.filter_by(
            user_id=user_id,
            is_active=True,
            is_deleted=False
        ).first()
    
    def deactivate_session(self, session_id):
        """Deactivate chat session"""
        try:
            session = ChatSession.query.filter_by(session_id=session_id).first()
            if session:
                session.is_active = False
                session.is_deleted = True
                session.deleted_at = datetime.utcnow()
                db.session.commit()
                self.logger.info(f"Successfully deactivated session {session_id}")
                return True
            else:
                self.logger.warning(f"No session found to deactivate: {session_id}")
                return False
        except Exception as e:
            self.logger.error(f"Error deactivating session {session_id}: {str(e)}")
            try:
                db.session.rollback()
            except:
                pass
            return False
    
    def delete_session_conversations(self, session_id):
        """Delete conversations for a session"""
        try:
            # First, find the chat session by session_id to get the integer ID
            chat_session = ChatSession.query.filter_by(session_id=session_id).first()
            if not chat_session:
                self.logger.warning(f"No chat session found for session_id: {session_id}")
                return True
            
            # Delete conversations using the chat_session.id (integer)
            conversations = Conversation.query.filter_by(session_id=chat_session.id).all()
            
            for conv in conversations:
                db.session.delete(conv)
            
            db.session.commit()
            self.logger.info(f"Deleted {len(conversations)} conversations for session {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting conversations for session {session_id}: {str(e)}")
            try:
                db.session.rollback()
            except:
                pass
            return False
    
    # Conversation Management
    def save_conversation(self, user_id, session_id, user_message, bot_response, data_sources=None, response_time=None):
        """Save conversation"""
        try:
            # Find the chat session by session_id to get the integer ID
            chat_session = ChatSession.query.filter_by(session_id=session_id).first()
            if not chat_session:
                self.logger.error(f"No chat session found for session_id: {session_id}")
                return None
            
            conversation = Conversation(
                user_id=user_id,
                session_id=chat_session.id,  # Use the integer ID from chat_session
                user_message=user_message,
                bot_response=bot_response,
                data_sources=data_sources,
                response_time=response_time
            )
            db.session.add(conversation)
            db.session.commit()
            self.logger.info(f"Saved conversation for user {user_id} in session {session_id}")
            return conversation
            
        except Exception as e:
            self.logger.error(f"Error saving conversation: {str(e)}")
            try:
                db.session.rollback()
            except:
                pass
            return None
    
    def get_conversation_history(self, user_id, limit=50):
        """Get conversation history for user"""
        return Conversation.query.filter_by(user_id=user_id).order_by(
            Conversation.created_at.desc()
        ).limit(limit).all()
    
    def get_session_conversations(self, session_id):
        """Get conversations for a session"""
        try:
            # First, find the chat session by session_id to get the integer ID
            chat_session = ChatSession.query.filter_by(session_id=session_id).first()
            if not chat_session:
                self.logger.warning(f"No chat session found for session_id: {session_id}")
                return []
            
            # Query conversations using the chat_session.id (integer)
            conversations = Conversation.query.filter_by(session_id=chat_session.id).order_by(
                Conversation.created_at.asc()
            ).all()
            
            self.logger.info(f"Retrieved {len(conversations)} conversations for session {session_id}")
            return conversations
            
        except Exception as e:
            self.logger.error(f"Failed to get session conversations for {session_id}: {str(e)}")
            return []
    
    # Company Information
    def get_company_info(self):
        """Get company information (static data)"""
        return {
            'company_name': 'Quantum Blue',
            'description': 'Advanced AI-powered chatbot for warehouse management and order processing',
            'features': [
                'Smart order placement',
                'Real-time inventory tracking',
                'AI-powered customer support',
                'Multi-warehouse management'
            ],
            'contact_info': {
                'email': 'support@quantumblue.com',
                'phone': '+1-800-QUANTUM',
                'address': '123 AI Street, Tech City, TC 12345'
            }
        }
    
    # Database Initialization
    def initialize_warehouses(self):
        """Initialize default warehouses"""
        warehouses = [
            {'location_name': 'Mumbai Central', 'city': 'Mumbai', 'state': 'Maharashtra', 'country': 'India'},
            {'location_name': 'Delhi North', 'city': 'Delhi', 'state': 'Delhi', 'country': 'India'},
            {'location_name': 'Bangalore South', 'city': 'Bangalore', 'state': 'Karnataka', 'country': 'India'},
            {'location_name': 'Chennai East', 'city': 'Chennai', 'state': 'Tamil Nadu', 'country': 'India'}
        ]
        
        for warehouse_data in warehouses:
            existing = Warehouse.query.filter_by(location_name=warehouse_data['location_name']).first()
            if not existing:
                warehouse = Warehouse(**warehouse_data)
                db.session.add(warehouse)
        
        db.session.commit()
        self.logger.info("Warehouses initialized")
    
    def create_sample_products(self):
        """Create sample products for testing"""
        warehouses = self.get_warehouses()
        if not warehouses:
            return
        
        sample_products = [
            {
                'product_code': 'QB001',
                'product_name': 'Quantum Processor',
                'product_description': 'High-performance quantum processor for AI applications',
                'price_of_product': 2500.00,
                'product_quantity': 100,
                'batch_number': 'QB2024001',
                'discount': 150.00,
                'scheme': 'Buy 2 Get 1 Free',
                'expiry_date': datetime(2025, 12, 31).date()
            },
            {
                'product_code': 'QB002',
                'product_name': 'Neural Network Module',
                'product_description': 'Advanced neural network processing module',
                'price_of_product': 1200.00,
                'product_quantity': 50,
                'batch_number': 'QB2024002',
                'discount': 100.00,
                'scheme': 'Buy 1 Get 20% Off',
                'expiry_date': datetime(2025, 10, 15).date()
            },
            {
                'product_code': 'QB003',
                'product_name': 'AI Memory Card',
                'product_description': 'High-speed memory card for AI operations',
                'price_of_product': 800.00,
                'product_quantity': 200,
                'batch_number': 'QB2024003',
                'discount': 50.00,
                'scheme': 'Buy 3 Get 2 Free',
                'expiry_date': datetime(2025, 8, 30).date()
            },
            {
                'product_code': 'QB004',
                'product_name': 'Quantum Sensors',
                'product_description': 'Advanced quantum sensing technology',
                'price_of_product': 1800.00,
                'product_quantity': 75,
                'batch_number': 'QB2024004',
                'discount': 200.00,
                'scheme': 'Buy 1 Get 15% Off',
                'expiry_date': datetime(2025, 11, 20).date()
            },
            {
                'product_code': 'QB005',
                'product_name': 'AI Controller',
                'product_description': 'Smart AI control unit for automation',
                'price_of_product': 950.00,
                'product_quantity': 120,
                'batch_number': 'QB2024005',
                'discount': 75.00,
                'scheme': 'Buy 2 Get 25% Off',
                'expiry_date': datetime(2025, 9, 10).date()
            }
        ]
        
        for warehouse in warehouses:
            for product_data in sample_products:
                existing = Product.query.filter_by(
                    product_code=product_data['product_code'],
                    warehouse_id=warehouse.id
                ).first()
                
                if not existing:
                    product = Product(
                        warehouse_id=warehouse.id,
                        **product_data
                    )
                    # Ensure all quantity fields are properly initialized
                    if product.product_quantity is None:
                        product.product_quantity = 0
                    if product.blocked_quantity is None:
                        product.blocked_quantity = 0
                    if product.available_for_sale is None:
                        product.available_for_sale = 0
                    
                    product.update_available_quantity()
                    db.session.add(product)
        
        db.session.commit()
        self.logger.info("Sample products created")
    
    def get_product_by_code(self, product_code):
        """Get product by product code"""
        return Product.query.filter_by(product_code=product_code).first()
    
    def get_product_pricing(self, product_id, quantity):
        """Get dynamic pricing for a product with discounts and schemes"""
        try:
            product = Product.query.get(product_id)
            if not product:
                return {
                    'final_price': 0,
                    'discount_percentage': 0,
                    'scheme_name': None,
                    'total_amount': 0,
                    'total_quantity': quantity,
                    'paid_quantity': quantity,
                    'free_quantity': 0,
                    'base_price': 0,
                    'discount_amount': 0
                }
            
            base_price = float(product.price_of_product)
            discount_amount = float(product.discount) if product.discount else 0
            scheme = product.scheme if product.scheme else None
            
            # Calculate discount percentage
            discount_percentage = 0
            if discount_amount > 0:
                discount_percentage = (discount_amount / base_price) * 100
            
            # Start with base price minus discount
            price_after_discount = base_price - discount_amount
            
            # Initialize scheme variables
            final_price = price_after_discount
            total_quantity = quantity
            paid_quantity = quantity
            free_quantity = 0
            
            # Apply scheme-based discounts
            if scheme:
                if 'Buy 3 Get 2 Free' in scheme and quantity >= 3:
                    # Buy 3 Get 2 Free: For every 5 items (3 paid + 2 free), user pays for 3
                    scheme_groups = quantity // 5
                    remaining_items = quantity % 5
                    
                    # Calculate free items from complete groups
                    free_quantity = scheme_groups * 2
                    paid_quantity = scheme_groups * 3
                    
                    # Handle remaining items
                    if remaining_items >= 3:
                        # If 3 or more remaining, apply another group
                        free_quantity += 2
                        paid_quantity += 3
                    else:
                        # If less than 3 remaining, user pays for all remaining
                        paid_quantity += remaining_items
                    
                    total_quantity = quantity  # User gets all items
                    # Price per paid item remains the same
                    final_price = price_after_discount
                elif 'Buy 2 Get 1 Free' in scheme and quantity >= 2:
                    # Buy 2 Get 1 Free: For every 2 items bought, get 1 free
                    # So for every 3 items total (2 paid + 1 free), user pays for 2
                    scheme_groups = quantity // 3  # Number of complete "Buy 2 Get 1 Free" groups
                    remaining_items = quantity % 3
                    
                    # Calculate free items: 1 free for every 3 items (2 paid + 1 free)
                    free_quantity = scheme_groups * 1
                    paid_quantity = scheme_groups * 2
                    
                    # Handle remaining items
                    if remaining_items >= 2:
                        # If 2 or more remaining, user pays for all remaining (no free item for incomplete group)
                        paid_quantity += remaining_items
                    elif remaining_items == 1:
                        # If 1 remaining, user pays for it (no free item for single item)
                        paid_quantity += 1
                    
                    total_quantity = quantity  # User gets all items they requested
                    # Price per paid item remains the same
                    final_price = price_after_discount
                elif 'Buy 1 Get 20% Off' in scheme and quantity >= 1:
                    # 20% off on all items
                    final_price = price_after_discount * 0.80
                    total_quantity = quantity
                    paid_quantity = quantity
                    free_quantity = 0
                elif 'Buy 1 Get 15% Off' in scheme and quantity >= 1:
                    # 15% off on all items
                    final_price = price_after_discount * 0.85
                    total_quantity = quantity
                    paid_quantity = quantity
                    free_quantity = 0
                elif 'Buy 2 Get 25% Off' in scheme and quantity >= 2:
                    # 25% off on all items
                    final_price = price_after_discount * 0.75
                    total_quantity = quantity
                    paid_quantity = quantity
                    free_quantity = 0
            
            # Calculate total amount based on paid quantity
            total_amount = final_price * paid_quantity
            
            result = {
                'final_price': round(final_price, 2),
                'discount_percentage': round(discount_percentage, 2),
                'scheme_name': scheme,
                'total_amount': round(total_amount, 2),
                'total_quantity': total_quantity,
                'paid_quantity': paid_quantity,
                'free_quantity': free_quantity,
                'base_price': round(base_price, 2),
                'discount_amount': round(discount_amount, 2)
            }
            
            self.logger.info(f"Pricing calculation for product {product_id} (qty {quantity}): final_price={final_price}, paid_quantity={paid_quantity}, total_amount={total_amount}")
            self.logger.info(f"Full result: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating pricing for product {product_id}: {str(e)}")
            # Return base pricing as fallback
            product = Product.query.get(product_id)
            if product:
                base_price = float(product.price_of_product)
                return {
                    'final_price': base_price,
                    'discount_percentage': 0,
                    'scheme_name': None,
                    'total_amount': base_price * quantity,
                    'total_quantity': quantity,
                    'paid_quantity': quantity,
                    'free_quantity': 0,
                    'base_price': round(base_price, 2),
                    'discount_amount': 0
                }
            return {
                'final_price': 0,
                'discount_percentage': 0,
                'scheme_name': None,
                'total_amount': 0,
                'total_quantity': quantity,
                'paid_quantity': quantity,
                'free_quantity': 0,
                'base_price': 0,
                'discount_amount': 0
            }
    
    def update_product_quantities(self, product_quantities):
        """Update product quantities after order selection"""
        try:
            for product_code, quantity in product_quantities.items():
                product = Product.query.filter_by(product_code=product_code).first()
                if product:
                    # Reduce available quantity
                    if product.available_for_sale >= quantity:
                        product.available_for_sale -= quantity
                        product.update_available_quantity()
                    else:
                        self.logger.warning(f"Insufficient stock for {product_code}: requested {quantity}, available {product.available_for_sale}")
            
            db.session.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error updating product quantities: {str(e)}")
            db.session.rollback()
            return False