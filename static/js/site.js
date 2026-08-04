/**
 * ETERNAAURA — Global Site Interactive Utilities
 * Handles Wishlist AJAX Toggling, CSRF token extraction, and UI sync.
 */

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

document.addEventListener('DOMContentLoaded', function() {
  const csrftoken = getCookie('csrftoken');

  // Global Wishlist Toggle Handler
  document.addEventListener('click', function(e) {
    const button = e.target.closest('[data-wishlist-toggle]');
    if (!button) return;

    e.preventDefault();
    const productId = button.getAttribute('data-product-id');
    if (!productId) return;

    fetch(`/wishlist/toggle/${productId}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken || '',
      },
    })
    .then(response => {
      if (response.status === 401) {
        return response.json().then(data => {
          window.location.href = data.redirect_url || '/account/login/';
        });
      }
      return response.json();
    })
    .then(data => {
      if (!data || !data.authenticated) return;

      // Synchronize all product buttons on the page with this product ID
      const matchingButtons = document.querySelectorAll(`[data-product-id="${productId}"]`);
      matchingButtons.forEach(btn => {
        const svg = btn.querySelector('svg');
        if (svg) {
          if (data.wishlisted) {
            svg.classList.add('fill-gold', 'text-gold');
          } else {
            svg.classList.remove('fill-gold', 'text-gold');
          }
        }
      });

      // Synchronize all Wishlist Count Badges on page
      const badges = document.querySelectorAll('[data-wishlist-count-badge]');
      badges.forEach(badge => {
        badge.textContent = data.count;
        if (data.count > 0) {
          badge.classList.remove('hidden');
        } else {
          badge.classList.add('hidden');
        }
      });
    })
    .catch(err => {
      console.error('Wishlist toggle error:', err);
    });

  });
});
