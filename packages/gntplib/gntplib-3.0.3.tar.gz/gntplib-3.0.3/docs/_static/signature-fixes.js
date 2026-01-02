/**
 * JavaScript fixes for long function/class signatures
 * MINIMAL approach - only add scroll indicators
 */

(function() {
    'use strict';
    
    /**
     * Add scroll indicator for long signatures
     */
    function addScrollIndicators() {
        const signatures = document.querySelectorAll('dt.sig, dt.sig-object');
        
        signatures.forEach(sig => {
            // Check if signature is scrollable
            if (sig.scrollWidth > sig.clientWidth) {
                // Add small indicator class
                sig.classList.add('sig-scrollable');
                
                // Add subtle visual cue in CSS instead of DOM manipulation
                sig.setAttribute('data-scrollable', 'true');
            }
        });
    }
    
    /**
     * Initialize - keep it simple
     */
    function init() {
        // Run on load
        addScrollIndicators();
        
        // Re-run on window resize
        let resizeTimer;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(addScrollIndicators, 250);
        });
    }
    
    // Run when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();