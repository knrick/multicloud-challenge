document.addEventListener('alpine:init', () => {
    Alpine.data('productForm', () => ({
        submitForm(event) {
            event.preventDefault();
            const formData = new FormData(event.target);
            const data = {
                name: formData.get('name'),
                description: formData.get('description'),
                price: parseFloat(formData.get('price')),
                stock: parseInt(formData.get('stock')),
                category: formData.get('category')
            };

            htmx.ajax('POST', '/api/products', {
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            }).then(() => {
                event.target.reset();
                // Refresh the product list
                htmx.trigger('#product-list', 'refresh');
            });
        }
    }));
}); 