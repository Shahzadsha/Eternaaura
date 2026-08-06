/**
 * ETERNAAURA — Global Site Interactive Utilities
 */

if (!window.__siteJsInitialized) {
  window.__siteJsInitialized = true;

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

  document.addEventListener('DOMContentLoaded', function () {
    // Global site utilities
  });

  /* --------------------------------------------------------------------
     Wishlist toggle — intercepts the wishlist form submit and does it
     via fetch() instead, so the page doesn't do a full reload. Falls
     back to a normal form submit if fetch fails for any reason.
     -------------------------------------------------------------------- */
  document.addEventListener('click', function (event) {
    const btn = event.target.closest('[data-wishlist-toggle]');
    if (!btn) return;

    const form = btn.closest('form');
    if (!form) return;

    event.preventDefault();

    if (btn.dataset.loading === 'true') return;
    btn.dataset.loading = 'true';

    const csrfToken = form.querySelector('input[name="csrfmiddlewaretoken"]')?.value || getCookie('csrftoken');

    fetch(form.action, {
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrfToken || '',
      },
    })
      .then(function (response) {
        if (response.status === 401) {
          return response.json().then(function (data) {
            window.location.href = data.login_url;
          });
        }
        if (!response.ok) {
          throw new Error('Wishlist toggle failed');
        }
        return response.json().then(function (data) {
          const productId = data.product_id || btn.dataset.productId;

          // Sync heart fill state across all buttons for this product on the page
          if (productId) {
            document.querySelectorAll('[data-wishlist-toggle][data-product-id="' + productId + '"]').forEach(function (targetBtn) {
              const icon = targetBtn.querySelector('svg');
              if (icon) {
                icon.classList.toggle('fill-gold', data.wishlisted);
                icon.classList.toggle('text-gold', data.wishlisted);
              }
            });
          } else {
            const icon = btn.querySelector('svg');
            if (icon) {
              icon.classList.toggle('fill-gold', data.wishlisted);
              icon.classList.toggle('text-gold', data.wishlisted);
            }
          }

          // Update every wishlist count badge on the page (navbar + sidebar)
          const count = (data.wishlist_count !== undefined) ? data.wishlist_count : data.count;
          if (count !== undefined) {
            document.querySelectorAll('[data-wishlist-count-badge]').forEach(function (badge) {
              badge.textContent = count;
              badge.classList.toggle('hidden', count === 0);
            });
          }
        });
      })
      .catch(function () {
        // Fallback: fall back to a normal full-page form submit
        form.submit();
      })
      .finally(function () {
        delete btn.dataset.loading;
      });
  });
}