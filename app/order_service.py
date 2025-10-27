import logging
from datetime import datetime
from flask import current_app
from app import db
from app.models import Order, OrderItem, Product, User
from app.database_service import DatabaseService
from app.email_utils import send_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderService:
    """Service for order management"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.logger = logger
    
    def create_order_from_cart(self, user_id, cart_items, warehouse_id, warehouse_location, user_email):
        """
        Create order from cart items
        """
        try:
            # Validate cart items
            validated_items = self._validate_cart_items(cart_items, warehouse_id)
            if not validated_items:
                return None, "Invalid cart items or insufficient stock"
            
            # Create order
            order = self.db_service.create_order(
                user_id=user_id,
                warehouse_id=warehouse_id,
                warehouse_location=warehouse_location,
                user_email=user_email
            )
            
            total_amount = 0
            
            # Add order items
            for item in validated_items:
                order_item = self.db_service.add_order_item(
                    order_id=order.id,
                    product_id=item['product_id'],
                    product_code=item['product_code'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price']
                )
                total_amount += order_item.total_price
                
                # Update product quantities
                self.db_service.update_product_quantities(
                    {item['product_code']: item['quantity']}
                )
            
            # Update order total
            order.total_amount = total_amount
            order.status = 'confirmed'
            db.session.commit()
            
            # Send confirmation emails
            self._send_order_confirmation_emails(order, user_email)
            
            self.logger.info(f"Order created successfully: {order.order_id}")
            return order, "Order created successfully"
            
        except Exception as e:
            self.logger.error(f"Error creating order: {str(e)}")
            db.session.rollback()
            return None, f"Error creating order: {str(e)}"
    
    def _validate_cart_items(self, cart_items, warehouse_id):
        """
        Validate cart items and check stock availability
        """
        validated_items = []
        
        for item in cart_items:
            product_code = item.get('product_code')
            quantity = item.get('quantity', 0)
            
            if not product_code or quantity <= 0:
                continue
            
            # Get product
            product = self.db_service.get_product_by_code_and_warehouse(
                product_code, warehouse_id
            )
            
            if not product:
                self.logger.warning(f"Product not found: {product_code}")
                continue
            
            if product.available_for_sale < quantity:
                self.logger.warning(f"Insufficient stock for {product_code}: requested {quantity}, available {product.available_for_sale}")
                continue
            
            validated_items.append({
                'product_id': product.id,
                'product_code': product_code,
                'quantity': quantity,
                'unit_price': product.price_of_product
            })
        
        return validated_items
    
    def _send_order_confirmation_emails(self, order, user_email):
        """
        Send order confirmation emails to user and admin
        """
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
    
    def _generate_order_confirmation_html(self, order, order_items, is_admin=False):
        """
        Generate HTML for order confirmation email
        """
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
    
    def get_order_status(self, order_id):
        """
        Get order status and details
        """
        try:
            order = self.db_service.get_order_by_id(order_id)
            if not order:
                return None, "Order not found"
            
            # Get order items
            order_items = []
            for item in order.order_items:
                order_items.append({
                    'product_code': item.product_code,
                    'product_name': item.product.product_name,
                    'quantity': item.product_quantity_ordered,
                    'unit_price': item.unit_price,
                    'total_price': item.total_price
                })
            
            order_details = {
                'order_id': order.order_id,
                'status': order.status,
                'total_amount': order.total_amount,
                'order_date': order.order_date.isoformat(),
                'warehouse_location': order.warehouse_location,
                'items': order_items
            }
            
            return order_details, "Order details retrieved"
            
        except Exception as e:
            self.logger.error(f"Error getting order status: {str(e)}")
            return None, f"Error retrieving order: {str(e)}"
    
    def update_order_status(self, order_id, new_status):
        """
        Update order status
        """
        try:
            order = self.db_service.update_order_status(order_id, new_status)
            if order:
                self.logger.info(f"Order {order_id} status updated to {new_status}")
                return order, "Order status updated"
            else:
                return None, "Order not found"
                
        except Exception as e:
            self.logger.error(f"Error updating order status: {str(e)}")
            return None, f"Error updating order: {str(e)}"
    
    def get_user_orders(self, user_id, limit=10):
        """
        Get user's order history
        """
        try:
            orders = self.db_service.get_orders_by_user(user_id)
            if limit:
                orders = orders[:limit]
            
            order_list = []
            for order in orders:
                order_list.append({
                    'order_id': order.order_id,
                    'status': order.status,
                    'total_amount': order.total_amount,
                    'order_date': order.order_date.isoformat(),
                    'warehouse_location': order.warehouse_location,
                    'item_count': len(order.order_items)
                })
            
            return order_list, "Orders retrieved successfully"
            
        except Exception as e:
            self.logger.error(f"Error getting user orders: {str(e)}")
            return [], f"Error retrieving orders: {str(e)}"
