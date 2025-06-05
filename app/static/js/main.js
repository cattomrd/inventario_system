// app/static/js/main.js

// Función para mostrar alertas
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('main.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto cerrar después de 5 segundos
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Validaciones de formulario
document.addEventListener('DOMContentLoaded', function() {
    // Validar fechas de garantía
    const purchaseDate = document.getElementById('purchase_date');
    const warrantyDate = document.getElementById('warranty_end_date');
    
    if (purchaseDate && warrantyDate) {
        purchaseDate.addEventListener('change', function() {
            warrantyDate.min = this.value;
        });
    }
    
    // Confirmación para eliminar
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('¿Está seguro de eliminar este registro?')) {
                e.preventDefault();
            }
        });
    });
    
    // Filtro de tabla en tiempo real
    const searchInput = document.getElementById('tableSearch');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const filter = this.value.toLowerCase();
            const table = document.querySelector('table');
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(filter) ? '' : 'none';
            });
        });
    }
    
    // Validación de número de serie único (simulada)
    const serialInput = document.getElementById('serial_number');
    if (serialInput) {
        serialInput.addEventListener('blur', function() {
            // Aquí podrías hacer una llamada AJAX para verificar si el serial existe
            // Por ahora solo validamos el formato
            const serial = this.value.trim();
            if (serial && serial.length < 5) {
                this.classList.add('is-invalid');
                showAlert('El número de serie debe tener al menos 5 caracteres', 'warning');
            } else {
                this.classList.remove('is-invalid');
            }
        });
    }
    
    // Mejorar la experiencia de selección múltiple
    const multiSelects = document.querySelectorAll('select[multiple]');
    multiSelects.forEach(select => {
        select.addEventListener('change', function() {
            const selected = Array.from(this.selectedOptions).map(opt => opt.text);
            const feedback = document.createElement('small');
            feedback.className = 'form-text text-muted';
            feedback.textContent = `Seleccionados: ${selected.join(', ')}`;
            this.parentNode.appendChild(feedback);
        });
    });
});

// Función para formatear fechas
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('es-ES', options);
}

// Función para calcular días hasta vencimiento de garantía
function daysUntilWarranty(warrantyDate) {
    const today = new Date();
    const warranty = new Date(warrantyDate);
    const diffTime = warranty - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) {
        return '<span class="text-danger">Vencida</span>';
    } else if (diffDays < 30) {
        return `<span class="text-warning">${diffDays} días</span>`;
    } else {
        return `<span class="text-success">${diffDays} días</span>`;
    }
}

// Exportar funciones para uso global
window.inventoryUtils = {
    showAlert,
    formatDate,
    daysUntilWarranty
};