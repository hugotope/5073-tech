/* TechShop - JavaScript per validacions del client i millores UX */

document.addEventListener('DOMContentLoaded', function() {
    
    // Validació de quantitat en els productes
    const quantityInputs = document.querySelectorAll('.quantity-input');
    
    quantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            const value = parseInt(this.value);
            const max = parseInt(this.getAttribute('max'));
            const min = parseInt(this.getAttribute('min'));
            
            if (isNaN(value) || value < min) {
                this.value = min;
                showMessage('La quantitat mínima és ' + min, 'error');
            } else if (value > max) {
                this.value = max;
                showMessage('No pots afegir més de ' + max + ' unitats', 'error');
            }
        });
        
        input.addEventListener('input', function() {
            const value = parseInt(this.value);
            const max = parseInt(this.getAttribute('max'));
            const min = parseInt(this.getAttribute('min'));
            
            if (value > max) {
                this.value = max;
            } else if (value < min && this.value !== '') {
                this.value = min;
            }
        });
    });
    
    // Validació de formularis add_to_cart
    const addToCartForms = document.querySelectorAll('.add-to-cart-form');
    
    addToCartForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const quantity = parseInt(this.querySelector('.quantity-input').value);
            
            if (isNaN(quantity) || quantity <= 0) {
                e.preventDefault();
                showMessage('Introdueix una quantitat vàlida', 'error');
                return false;
            }
            
            if (quantity > 5) {
                e.preventDefault();
                showMessage('No pots afegir més de 5 unitats', 'error');
                return false;
            }
        });
    });
    
    // Auto-hide flash messages després de 5 segons
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            message.style.transition = 'opacity 0.5s';
            setTimeout(() => {
                message.remove();
            }, 500);
        }, 5000);
    });
    
});

/**
 * Mostra un missatge temporal a l'usuari
 */
function showMessage(text, type = 'info') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `flash-message flash-${type}`;
    messageDiv.textContent = text;
    messageDiv.style.position = 'fixed';
    messageDiv.style.top = '80px';
    messageDiv.style.right = '20px';
    messageDiv.style.zIndex = '10000';
    messageDiv.style.minWidth = '300px';
    
    document.body.appendChild(messageDiv);
    
    setTimeout(() => {
        messageDiv.style.opacity = '0';
        messageDiv.style.transition = 'opacity 0.5s';
        setTimeout(() => {
            messageDiv.remove();
        }, 500);
    }, 3000);
}

/**
 * Valida un camp d'entrada
 */
function validateField(input) {
    const value = input.value.trim();
    const minLength = input.getAttribute('minlength');
    const maxLength = input.getAttribute('maxlength');
    const pattern = input.getAttribute('pattern');
    
    // Validar longitud
    if (minLength && value.length < parseInt(minLength)) {
        return false;
    }
    
    if (maxLength && value.length > parseInt(maxLength)) {
        return false;
    }
    
    // Validar patró
    if (pattern && value) {
        const regex = new RegExp(pattern);
        if (!regex.test(value)) {
            return false;
        }
    }
    
    return true;
}

/**
 * Valida un email
 */
function validateEmail(email) {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailRegex.test(email);
}

