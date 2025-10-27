import logging
from datetime import datetime
from flask import current_app, session
from app import db
from app.models import Order, OrderItem, Product, User, Warehouse
from app.database_service import DatabaseService
from app.email_utils import send_email
import json
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedOrderService:
    """Enhanced service for professional order management with improved state handling"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.logger = logger
    
    def initialize_cart_session(self, user_id, warehouse_id):
        """Initialize a new cart session with proper state management"""
        try:
            cart_id = str(uuid.uuid4())
            cart_session = {
                'cart_id': cart_id,
                'user_id': user_id,
                'warehouse_id': warehouse_id,
                'items': [],
                'status': 'active',
                'created_at': datetime.utcnow().isoformat(),
                'last_updated': datetime.utcnow().isoformat(),
                'total_amount': 0,
                'discount_applied': 0,
                'final_total': 0,
                'session_data': {}
            }
            
            # Store in session
            if 'order_session' not in session:
                session['order_session'] = {}
            
            session['order_session'].update(cart_session)
            session['order_session']['cart_id'] = cart_id
            
            self.logger.info(f"Cart session initialized: {cart_id}")
            return cart_id, "Cart session initialized successfully"
            
        except Exception as e:
            self.logger.error(f"Error initializing cart session: {str(e)}")
            return None, f"Error initializing cart: {str(e)}"
    
    def add_item_to_cart(self, product_code, quantity, user_id, warehouse_id):
        """Add item to cart with proper validation and state management"""
        try:
            # Get product details
            product = self.db_service.get_product_by_code_and_warehouse(product_code, warehouse_id)
            if not product:
                return False, f"Product {product_code} not found in warehouse"
            
            # Check availability
            if product.available_for_sale < quantity:
                return False, f"Insufficient stock. Available: {product.available_for_sale}, Requested: {quantity}"
            
            # Get pricing information
            pricing_info = self.db_service.get_product_pricing(product.id, quantity)
            
            # Create cart item
            cart_item = {
                'product_id': product.id,
                'product_code': product_code,
                'product_name': product.product_name,
                'quantity': quantity,
                'unit_price': pricing_info['base_price'],
                'final_price': pricing_info['final_price'],
                'discount_percentage': pricing_info['discount_percentage'],
                'scheme_name': pricing_info['scheme_name'],
                'item_total': pricing_info['total_amount'],
                'added_at': datetime.utcnow().isoformat()
            }
            
            # Update cart session
            if 'order_session' not in session:
                self.initialize_cart_session(user_id, warehouse_id)
            
            order_session = session['order_session']
            
            # Check if item already exists in cart
            existing_item_index = None
            for i, item in enumerate(order_session['items']):
                if item['product_code'] == product_code:
                    existing_item_index = i
                    break
            
            if existing_item_index is not None:
                # Update existing item
                order_session['items'][existing_item_index]['quantity'] += quantity
                order_session['items'][existing_item_index]['item_total'] += pricing_info['total_amount']
            else:
                # Add new item
                order_session['items'].append(cart_item)
            
            # Recalculate totals
            self._recalculate_cart_totals(order_session)
            order_session['last_updated'] = datetime.utcnow().isoformat()
            
            session['order_session'] = order_session
            
            self.logger.info(f"Item added to cart: {product_code} x {quantity}")
            return True, f"Added {quantity}x {product.product_name} to cart"
            
        except Exception as e:
            self.logger.error(f"Error adding item to cart: {str(e)}")
            return False, f"Error adding item: {str(e)}"
    
    def remove_item_from_cart(self, product_code):
        """Remove item from cart"""
        try:
            if 'order_session' not in session:
                return False, "No active cart session"
            
            order_session = session['order_session']
            
            # Find and remove item
            original_length = len(order_session['items'])
            order_session['items'] = [item for item in order_session['items'] if item['product_code'] != product_code]
            
            if len(order_session['items']) == original_length:
                return False, f"Product {product_code} not found in cart"
            
            # Recalculate totals
            self._recalculate_cart_totals(order_session)
            order_session['last_updated'] = datetime.utcnow().isoformat()
            
            session['order_session'] = order_session
            
            self.logger.info(f"Item removed from cart: {product_code}")
            return True, f"Removed {product_code} from cart"
            
        except Exception as e:
            self.logger.error(f"Error removing item from cart: {str(e)}")
            return False, f"Error removing item: {str(e)}"
    
    def update_item_quantity(self, product_code, new_quantity):
        """Update item quantity in cart"""
        try:
            if 'order_code' not in session:
                return False, "No active cart session"
            
            order_session = session['order_session']
            
            # Find item and update quantity
            for item in order_session['items']:
                if item['product_code'] == product_code:
                    if new_quantity <= 0:
                        return self.remove_item_from_cart(product_code)
                    
                    # Check stock availability
                    product = self.db_service.get_product_by_code(item['product_code'])
                    if product and product.available_for_sale < new_quantity:
                        return False, f"Insufficient stock. Available: {product.available_for_sale}"
                    
                    # Update quantity and recalculate pricing
                    old_quantity = item['quantity']
                    item['quantity'] = new_quantity
                    
                    # Recalculate item pricing
                    pricing_info = self.db_service.get_product_pricing(item['product_id'], new_quantity)
                    item['final_price'] = pricing_info['final_price']
                    item['discount_percentage'] = pricing_info['discount_percentage']
                    item['scheme_name'] = pricing_info['scheme_name']
                    item['item_total'] = pricing_info['total_amount']
                    
                    # Recalculate cart totals
                    self._recalculate_cart_totals(order_session)
                    order_session['last_updated'] = datetime.utcnow().isoformat()
                    
                    session['order_session'] = order_session
                    
                    self.logger.info(f"Updated quantity for {product_code}: {old_quantity} -> {new_quantity}")
                    return True, f"Updated {product_code} quantity to {new_quantity}"
            
            return False, f"Product {product_code} not found in cart"
            
        except Exception as e:
            self.logger.error(f"Error updating item quantity: {str(e)}")
            return False, f"Error updating quantity: {str(e)}"
    
    def get_cart_summary(self):
        """Get current cart summary with detailed information"""
        try:
            if 'order_session' not in session:
                return None, "No active cart session"
            
            order_session = session['order_session']
            
            if not order_session['items']:
                return {
                    'items': [],
                    'total_amount': 0,
                    'item_count': 0,
                    'status': 'empty'
                }, "Cart is empty"
            
            # Format cart items for display
            formatted_items = []
            for item in order_session['items']:
                formatted_items.append({
                    'product_code': item['product_code'],
                    'product_name': item['product_name'],
                    'quantity': item['quantity'],
                    'unit_price': item['unit_price'],
                    'final_price': item['final_price'],
                    'discount_percentage': item['discount_percentage'],
                    'scheme_name': item['scheme_name'],
                    'item_total': item['item_total']
                })
            
            cart_summary = {
                'cart_id': order_session.get('cart_id'),
                'items': formatted_items,
                'total_amount': order_session['total_amount'],
                'discount_applied': order_session['discount_applied'],
                'final_total': order_session['final_total'],
                'item_count': len(order_session['items']),
                'status': 'active',
                'last_updated': order_session['last_updated']
            }
            
            return cart_summary, "Cart summary retrieved successfully"
            
        except Exception as e:
            self.logger.error(f"Error getting cart summary: {str(e)}")
            return None, f"Error retrieving cart: {str(e)}"
    
    def confirm_cart(self, user_id, warehouse_id, user_email):
        """Confirm cart and create order with enhanced validation"""
        try:
            if 'order_session' not in session:
                return None, "No active cart session"
            
            order_session = session['order_session']
            
            if not order_session['items']:
                return None, "Cart is empty"
            
            # Validate all items are still available
            for item in order_session['items']:
                product = self.db_service.get_product_by_code_and_warehouse(item['product_code'], warehouse_id)
                if not product:
                    return None, f"Product {item['product_code']} no longer available"
                
                if product.available_for_sale < item['quantity']:
                    return None, f"Insufficient stock for {item['product_code']}. Available: {product.available_for_sale}, Required: {item['quantity']}"
            
            # Create order
            order = self.db_service.create_order(
                user_id=user_id,
                warehouse_id=warehouse_id,
                warehouse_location=session.get('warehouse_location'),
                user_email=user_email
            )
            
            if not order:
                return None, "Failed to create order"
            
            # Add order items
            total_amount = 0
            for item in order_session['items']:
                order_item = self.db_service.add_order_item(
                    order_id=order.id,
                    product_id=item['product_id'],
                    product_code=item['product_code'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price']
                )
                total_amount += order_item.total_price
                
                # Update product quantities
                self.db_service.update_product_quantities({
                    item['product_code']: item['quantity']
                })
            
            # Update order total and status
            order.total_amount = total_amount
            order.status = 'confirmed'
            db.session.commit()
            
            # Update session
            order_session['status'] = 'completed'
            order_session['order_id'] = order.order_id
            order_session['pending_confirmation'] = False
            session['order_session'] = order_session
            
            # Send confirmation emails
            self._send_order_confirmation_emails(order, user_email)
            
            self.logger.info(f"Order confirmed successfully: {order.order_id}")
            return order, "Order confirmed successfully"
            
        except Exception as e:
            self.logger.error(f"Error confirming cart: {str(e)}")
            db.session.rollback()
            return None, f"Error confirming order: {str(e)}"
    
    def clear_cart(self):
        """Clear current cart session"""
        try:
            # Force clear the entire order session
            session['order_session'] = {
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
            
            # Force session to be saved
            session.modified = True
            
            self.logger.info("Cart cleared successfully - session reset")
            return True, "Cart cleared successfully"
            
        except Exception as e:
            self.logger.error(f"Error clearing cart: {str(e)}")
            return False, f"Error clearing cart: {str(e)}"
    
    def force_clear_cart(self):
        """Force clear cart and reset session completely"""
        try:
            # Remove the entire order session
            if 'order_session' in session:
                del session['order_session']
            
            # Create a completely fresh session
            session['order_session'] = {
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
            
            # Force session to be saved
            session.modified = True
            
            self.logger.info("Cart force cleared - complete session reset")
            return True, "Cart force cleared successfully"
            
        except Exception as e:
            self.logger.error(f"Error force clearing cart: {str(e)}")
            return False, f"Error force clearing cart: {str(e)}"
    
    def _recalculate_cart_totals(self, order_session):
        """Recalculate cart totals based on current items"""
        try:
            total_cost = 0
            discount_applied = 0
            
            for item in order_session['items']:
                total_cost += item['item_total']
                if item['discount_percentage'] > 0:
                    discount_amount = (item['unit_price'] - item['final_price']) * item['quantity']
                    discount_applied += discount_amount
            
            order_session['total_cost'] = total_cost
            order_session['discount_applied'] = discount_applied
            order_session['final_total'] = total_cost
            
        except Exception as e:
            self.logger.error(f"Error recalculating cart totals: {str(e)}")
    
    def _send_order_confirmation_emails(self, order, user_email):
        """Send order confirmation emails"""
        try:
            # Get order details
            order_items = []
            for item in order.order_items:
                order_items.append({
                    'product_code': item.product_code,
                    'product_name': item.product.product_name,
                    'quantity': item.product_quantity_ordered,
                    'unit_price': item.unit_price,
                    'total_price': item.total_price
                })
            
            # Email to user
            user_subject = f"Order Confirmation - {order.order_id}"
            user_html = self._generate_order_confirmation_html(order, order_items, is_admin=False)
            send_email(user_email, user_subject, user_html, 'order_confirmation')
            
            # Email to admin
            admin_email = current_app.config.get('ADMIN_EMAIL')
            if admin_email:
                admin_subject = f"[Admin] New Order - {order.order_id}"
                admin_html = self._generate_order_confirmation_html(order, order_items, is_admin=True)
                send_email(admin_email, admin_subject, admin_html, 'order_admin')
            
            self.logger.info(f"Order confirmation emails sent for order {order.order_id}")
            
        except Exception as e:
            self.logger.error(f"Error sending order emails: {str(e)}")
    
    def create_order_from_cart(self, user_id, cart_items, warehouse_id, warehouse_location, user_email):
        """Create order from cart items - compatibility method for chatbot integration"""
        try:
            if not cart_items:
                return None, "No items in cart"
            
            # Validate all items are still available
            for item in cart_items:
                product = self.db_service.get_product_by_code_and_warehouse(item['product_code'], warehouse_id)
                if not product:
                    return None, f"Product {item['product_code']} no longer available"
                
                if product.available_for_sale < item['quantity']:
                    return None, f"Insufficient stock for {item['product_code']}. Available: {product.available_for_sale}, Required: {item['quantity']}"
            
            # Create order
            order = self.db_service.create_order(
                user_id=user_id,
                warehouse_id=warehouse_id,
                warehouse_location=warehouse_location,
                user_email=user_email
            )
            
            if not order:
                return None, "Failed to create order"
            
            # Add order items
            total_amount = 0
            for item in cart_items:
                # Get product details
                product = self.db_service.get_product_by_code(item['product_code'])
                if product:
                    # Calculate pricing with discounts and schemes
                    pricing_info = self.db_service.get_product_pricing(product.id, item['quantity'])
                    
                    order_item = self.db_service.add_order_item(
                        order_id=order.id,
                        product_id=product.id,
                        product_code=item['product_code'],
                        quantity=item['quantity'],
                        unit_price=pricing_info['final_price'],  # Use final price with discounts
                        total_price=pricing_info['total_amount']  # Use the calculated total amount
                    )
                    # Use the calculated total amount from pricing info
                    total_amount += pricing_info['total_amount']
                    
                    # Update product quantities
                    self.db_service.update_product_quantities({
                        item['product_code']: item['quantity']
                    })
            
            # Update order total and status
            order.total_amount = total_amount
            order.status = 'confirmed'
            db.session.commit()
            
            # Send confirmation emails
            self._send_order_confirmation_emails(order, user_email)
            
            self.logger.info(f"Order created successfully: {order.order_id}")
            return order, "Order created successfully"
            
        except Exception as e:
            self.logger.error(f"Error creating order from cart: {str(e)}")
            db.session.rollback()
            return None, f"Error creating order: {str(e)}"

    def _generate_order_confirmation_html(self, order, order_items, is_admin=False):
        """Generate HTML for order confirmation email"""
        recipient = "Admin" if is_admin else "Customer"
        
        items_html = ""
        for item in order_items:
            items_html += f"""
            <tr>
                <td>{item['product_code']}</td>
                <td>{item['product_name']}</td>
                <td>{item['quantity']}</td>
                <td>${item['unit_price']:.2f}</td>
                <td>${item['total_price']:.2f}</td>
            </tr>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
                .content {{ background: white; padding: 20px; border-radius: 8px; margin-top: 20px; }}
                .order-details {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .total {{ font-size: 18px; font-weight: bold; color: #007bff; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Order Confirmation</h1>
                    <p>Thank you for your order with Quantum Blue!</p>
                </div>
                
                <div class="content">
                    <h2>Order Details</h2>
                    <div class="order-details">
                        <p><strong>Order ID:</strong> {order.order_id}</p>
                        <p><strong>Date:</strong> {order.order_date.strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p><strong>Status:</strong> {order.status.title()}</p>
                        <p><strong>Warehouse:</strong> {order.warehouse_location}</p>
                        <p><strong>Customer Email:</strong> {order.user_email}</p>
                    </div>
                    
                    <h3>Order Items</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Product Code</th>
                                <th>Product Name</th>
                                <th>Quantity</th>
                                <th>Unit Price</th>
                                <th>Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                        </tbody>
                    </table>
                    
                    <div class="total">
                        <strong>Total Amount: ${order.total_amount:.2f}</strong>
                    </div>
                    
                    <p>We'll process your order and send you updates via email.</p>
                    
                    <p>Thank you for choosing Quantum Blue!</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
