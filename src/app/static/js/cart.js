// Cart management
class CartManager {
    constructor() {
        this.cart = JSON.parse(localStorage.getItem('cart')) || [];
        this.updateCartCount();
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Add event listeners to all Add to Cart buttons
        document.addEventListener('DOMContentLoaded', () => {
            // Product page event listeners
            const addToCartButtons = document.querySelectorAll('.add-to-cart-btn');
            addToCartButtons.forEach(button => {
                button.addEventListener('click', (e) => {
                    const button = e.target.closest('.add-to-cart-btn');
                    if (!button) return;
                    
                    const productId = button.dataset.productId;
                    const productName = button.dataset.productName;
                    const productPrice = parseFloat(button.dataset.productPrice);
                    const quantity = parseInt(document.getElementById(`quantity-${productId}`).value);
                    this.addToCart(productId, productName, productPrice, quantity);
                });
            });

            // Cart page event listeners
            const cartItems = document.getElementById('cart-items');
            if (cartItems) {
                cartItems.addEventListener('click', (e) => {
                    const removeButton = e.target.closest('.remove-from-cart-btn');
                    if (!removeButton) return;
                    
                    const productId = removeButton.dataset.productId;
                    this.removeFromCart(productId);
                });

                // Initialize cart display
                this.updateCart();
            }
        });
    }

    addToCart(productId, productName, price, quantity) {
        if (quantity < 1) return;

        const existingItem = this.cart.find(item => item.id === productId);
        if (existingItem) {
            existingItem.quantity += quantity;
        } else {
            this.cart.push({
                id: productId,
                name: productName,
                price: price,
                quantity: quantity
            });
        }

        localStorage.setItem('cart', JSON.stringify(this.cart));
        this.updateCartCount();
        
        // Show feedback
        alert(`Added ${quantity} ${productName} to cart!`);
    }

    removeFromCart(productId) {
        this.cart = this.cart.filter(item => item.id !== productId);
        localStorage.setItem('cart', JSON.stringify(this.cart));
        this.updateCart();
    }

    updateCartCount() {
        const count = this.cart.reduce((total, item) => total + item.quantity, 0);
        const cartCount = document.getElementById('cart-count');
        if (cartCount) {
            cartCount.textContent = count;
        }
    }

    updateCart() {
        this.updateCartCount();
        
        const cartItems = document.getElementById('cart-items');
        const checkoutButton = document.getElementById('checkout-button');
        
        if (!cartItems) return; // Not on cart page

        if (this.cart.length === 0) {
            cartItems.innerHTML = `
                <div class="text-center py-8">
                    <p class="text-gray-500 mb-4">Your cart is empty</p>
                    <a href="/products" class="text-blue-500 hover:text-blue-600">Continue Shopping</a>
                </div>
            `;
            if (checkoutButton) {
                checkoutButton.disabled = true;
            }
            this.updateTotals(0);
            return;
        }

        if (checkoutButton) {
            checkoutButton.disabled = false;
        }
        
        // Render cart items
        cartItems.innerHTML = this.cart.map(item => `
            <div class="flex items-center justify-between py-4 border-b last:border-0">
                <div>
                    <h3 class="font-medium">${item.name}</h3>
                    <p class="text-sm text-gray-500">$${item.price.toFixed(2)} × ${item.quantity}</p>
                </div>
                <div class="flex items-center space-x-4">
                    <span class="font-medium">$${(item.price * item.quantity).toFixed(2)}</span>
                    <button class="remove-from-cart-btn text-red-500 hover:text-red-600"
                            data-product-id="${item.id}">
                        Remove
                    </button>
                </div>
            </div>
        `).join('');

        // Update totals
        const subtotal = this.cart.reduce((total, item) => total + (item.price * item.quantity), 0);
        this.updateTotals(subtotal);
    }

    updateTotals(subtotal) {
        const tax = subtotal * 0.1;
        const total = subtotal + tax;

        const subtotalElement = document.getElementById('subtotal');
        const taxElement = document.getElementById('tax');
        const totalElement = document.getElementById('total');

        if (subtotalElement) subtotalElement.textContent = `$${subtotal.toFixed(2)}`;
        if (taxElement) taxElement.textContent = `$${tax.toFixed(2)}`;
        if (totalElement) totalElement.textContent = `$${total.toFixed(2)}`;
    }

    async checkout(email) {
        try {
            const response = await fetch('/api/orders', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    userEmail: email,
                    items: this.cart.map(item => ({
                        productId: item.id,
                        quantity: item.quantity,
                        price: item.price
                    })),
                    total: this.cart.reduce((total, item) => total + (item.price * item.quantity), 0)
                })
            });

            if (!response.ok) {
                throw new Error('Failed to create order');
            }

            // Clear cart and redirect to orders page
            localStorage.removeItem('cart');
            window.location.href = '/orders';
        } catch (error) {
            alert('Error creating order: ' + error.message);
        }
    }
}

// Initialize cart manager
const cartManager = new CartManager(); 