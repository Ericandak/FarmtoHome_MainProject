
$(document).ready(function() {
    // Coupon application handling
    const csrfToken = $('meta[name="csrf-token"]').attr('content');
    $('#apply-coupon').click(function() {
        const couponCode = $('#coupon-code').val().trim();
        if (!couponCode) {
            showCouponMessage('Please enter a coupon code', 'danger');
            return;
        }

        // Send AJAX request to verify and apply coupon
        $.ajax({
            url: '/products/apply-coupon/',
            type: 'POST',
            data: JSON.stringify({
                'coupon_code': couponCode
            }),
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': csrfToken
            },
            success: function(response) {
                if (response.status === 'success') {
                    // Update the cart summary
                    const subtotal = parseFloat(response.subtotal);
                    const discount = parseFloat(response.discount);
                    const total = subtotal - discount;

                    $('#cart-subtotal').text('₹' + subtotal.toFixed(2));
                    $('#discount-amount').text('₹' + discount.toFixed(2));
                    $('#cart-total').text('₹' + total.toFixed(2));
                    $('#applied-coupon').val(couponCode);

                    showCouponMessage(response.message, 'success');
                    
                    // Disable the coupon input and button
                    $('#coupon-code').prop('disabled', true);
                    $('#apply-coupon').prop('disabled', true);
                } else {
                    showCouponMessage(response.message, 'danger');
                }
            },
            error: function(xhr, status, error) {
                console.error("Error applying coupon:", error);
                showCouponMessage("An error occurred while applying the coupon. Please try again.", 'danger');
            }
        });
    });

    // Function to show coupon messages
    function showCouponMessage(message, type) {
        const messageDiv = $('#coupon-message');
        messageDiv.html(`<div class="alert alert-${type}" role="alert">${message}</div>`);
        
        // Auto-hide the message after 5 seconds
        setTimeout(function() {
            messageDiv.html('');
        }, 5000);
    }

    // Add coupon code to checkout form submission
    $('a[href*="checkout"]').click(function(e) {
        const appliedCoupon = $('#applied-coupon').val();
        console.log(appliedCoupon)
        if (appliedCoupon) {
            const currentHref = $(this).attr('href');
            const separator = currentHref.includes('?') ? '&' : '?';
            
            // Get the discount amount without the currency symbol
            const discountAmount = $('#discount-amount').text().replace('₹', '').trim();
            
            // Get the final total without the currency symbol
            const finalTotal = $('#cart-total').text().replace('₹', '').trim();
            
            console.log('Applying coupon:', {
                coupon: appliedCoupon,
                discount: discountAmount,
                finalTotal: finalTotal
            });
            
            // Pass coupon code, discount amount, and final total to checkout
            $(this).attr('href', currentHref + separator + 
                'coupon=' + encodeURIComponent(appliedCoupon) + 
                '&discount=' + encodeURIComponent(discountAmount) +
                '&final_total=' + encodeURIComponent(finalTotal));
        }
    });
});