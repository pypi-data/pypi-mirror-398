/* FastroAI Documentation JavaScript Enhancements */

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  initializeFeatures();
  setupCodeBlockEnhancements();
  setupAPIExamples();
  setupAnimations();
});

// Also initialize after navigation (for instant navigation)
document.addEventListener('DOMContentLoaded', function() {
  const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.type === 'childList') {
        // Re-add copy buttons after content changes
        setTimeout(addCopyButtons, 100);
      }
    });
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
});

/**
 * Initialize all documentation features
 */
function initializeFeatures() {
  // Add copy buttons to code blocks
  addCopyButtons();
  
  // Setup tab switching for multi-option content
  setupTabs();
  
  // Initialize tooltips
  initializeTooltips();
  
  // Setup search enhancements
  enhanceSearch();
}

/**
 * Add copy buttons to code blocks (but only if they don't already have one)
 */
function addCopyButtons() {
  // Wait for content to be loaded
  const codeBlocks = document.querySelectorAll('pre code');
  
  console.log(`Found ${codeBlocks.length} code blocks`); // Debug log
  
  codeBlocks.forEach(block => {
    const pre = block.parentElement;
    
    // Skip if already has a copy button
    if (pre.querySelector('.copy-button')) {
      return;
    }
    
    const button = document.createElement('button');
    
    button.className = 'copy-button';
    button.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
      </svg>
    `;
    button.title = 'Copy to clipboard';
    
    button.addEventListener('click', (e) => {
      e.preventDefault();
      copyToClipboard(block.textContent, button);
    });
    
    pre.style.position = 'relative';
    pre.appendChild(button);
    
    console.log('Added copy button to code block'); // Debug log
  });
}

/**
 * Copy text to clipboard with visual feedback
 */
async function copyToClipboard(text, button) {
  try {
    await navigator.clipboard.writeText(text);
    
    // Visual feedback
    const original = button.innerHTML;
    button.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="20,6 9,17 4,12"></polyline>
      </svg>
    `;
    button.style.color = '#10b981';
    
    setTimeout(() => {
      button.innerHTML = original;
      button.style.color = '';
    }, 2000);
    
  } catch (err) {
    console.error('Failed to copy text: ', err);
  }
}

/**
 * Setup tabbed content functionality
 */
function setupTabs() {
  const tabGroups = document.querySelectorAll('.tabbed-set');
  
  tabGroups.forEach(group => {
    const inputs = group.querySelectorAll('input[type="radio"]');
    const labels = group.querySelectorAll('label');
    
    labels.forEach(label => {
      label.addEventListener('click', function() {
        const targetInput = document.getElementById(this.getAttribute('for'));
        if (targetInput) {
          targetInput.checked = true;
          updateTabContent(group);
        }
      });
    });
  });
}

/**
 * Update tab content visibility
 */
function updateTabContent(tabGroup) {
  const contents = tabGroup.querySelectorAll('.tabbed-content');
  const activeInput = tabGroup.querySelector('input[type="radio"]:checked');
  
  contents.forEach((content, index) => {
    content.style.display = index === Array.from(tabGroup.querySelectorAll('input[type="radio"]')).indexOf(activeInput) ? 'block' : 'none';
  });
}

/**
 * Setup code block enhancements
 */
function setupCodeBlockEnhancements() {
  // Add language labels to code blocks
  const codeBlocks = document.querySelectorAll('pre code[class*="language-"]');
  
  codeBlocks.forEach(block => {
    const className = block.className;
    const language = className.match(/language-(\w+)/)?.[1];
    
    if (language) {
      const label = document.createElement('div');
      label.className = 'code-language-label';
      label.textContent = language.toUpperCase();
      
      const pre = block.parentElement;
      pre.insertBefore(label, block);
    }
  });
}

/**
 * Setup interactive API examples
 */
function setupAPIExamples() {
  const apiBlocks = document.querySelectorAll('.api-example');
  
  apiBlocks.forEach(block => {
    const tryButton = document.createElement('button');
    tryButton.className = 'api-try-button';
    tryButton.textContent = 'Try this endpoint';
    tryButton.addEventListener('click', () => openAPITester(block));
    
    block.appendChild(tryButton);
  });
}

/**
 * Open API testing interface
 */
function openAPITester(apiBlock) {
  // This would integrate with the actual API documentation
  // For now, just show a modal or redirect to the interactive docs
  const endpoint = apiBlock.dataset.endpoint;
  if (endpoint) {
    window.open(`http://localhost:8000/docs#${endpoint}`, '_blank');
  }
}

/**
 * Initialize tooltips for technical terms
 */
function initializeTooltips() {
  const tooltipElements = document.querySelectorAll('[data-tooltip]');
  
  tooltipElements.forEach(element => {
    element.addEventListener('mouseenter', showTooltip);
    element.addEventListener('mouseleave', hideTooltip);
  });
}

/**
 * Show tooltip
 */
function showTooltip(event) {
  const element = event.target;
  const tooltipText = element.dataset.tooltip;
  
  const tooltip = document.createElement('div');
  tooltip.className = 'custom-tooltip';
  tooltip.textContent = tooltipText;
  
  document.body.appendChild(tooltip);
  
  const rect = element.getBoundingClientRect();
  tooltip.style.left = `${rect.left + rect.width / 2}px`;
  tooltip.style.top = `${rect.top - tooltip.offsetHeight - 8}px`;
  
  element._tooltip = tooltip;
}

/**
 * Hide tooltip
 */
function hideTooltip(event) {
  const element = event.target;
  if (element._tooltip) {
    document.body.removeChild(element._tooltip);
    element._tooltip = null;
  }
}

/**
 * Setup animations and scroll effects
 */
function setupAnimations() {
  // Animate elements on scroll
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-in');
      }
    });
  }, observerOptions);
  
  // Observe all feature cards and important sections
  const animateElements = document.querySelectorAll('.grid.cards .card, .feature-highlight, .quick-start');
  animateElements.forEach(el => {
    el.classList.add('animate-target');
    observer.observe(el);
  });
}

/**
 * Enhance search functionality
 */
function enhanceSearch() {
  const searchInput = document.querySelector('[data-md-component="search-query"]');
  if (!searchInput) return;
  
  // Add search suggestions
  searchInput.addEventListener('input', debounce(handleSearchInput, 300));
}

/**
 * Handle search input with suggestions
 */
function handleSearchInput(event) {
  const query = event.target.value.toLowerCase();
  if (query.length < 2) return;
  
  // Common search terms and their suggested pages
  const suggestions = {
    'ai': 'features/ai-integration/',
    'auth': 'features/authentication/',
    'payment': 'features/payment-system/',
    'stripe': 'features/payment-system/stripe-integration/',
    'docker': 'getting-started/docker-guide/',
    'setup': 'getting-started/',
    'config': 'configuration/',
    'deploy': 'deployment/'
  };
  
  // This would show search suggestions in a dropdown
  // Implementation depends on the search system used
}

/**
 * Debounce utility function
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Add version selector if multiple versions exist
 */
function setupVersionSelector() {
  const versions = ['v1.0', 'v1.1', 'latest'];
  
  if (versions.length > 1) {
    const selector = document.createElement('select');
    selector.className = 'version-selector';
    
    versions.forEach(version => {
      const option = document.createElement('option');
      option.value = version;
      option.textContent = version;
      if (version === 'latest') option.selected = true;
      selector.appendChild(option);
    });
    
    selector.addEventListener('change', (e) => {
      // Handle version switching
      const newVersion = e.target.value;
      console.log(`Switching to version: ${newVersion}`);
    });
    
    // Add to header or navigation
    const header = document.querySelector('.md-header');
    if (header) {
      header.appendChild(selector);
    }
  }
}

/**
 * Track documentation analytics
 */
function trackDocumentationUsage() {
  // Track page views and popular sections
  const currentPage = window.location.pathname;
  
  // Track time on page
  const startTime = Date.now();
  
  window.addEventListener('beforeunload', () => {
    const timeSpent = Date.now() - startTime;
    console.log(`Time spent on ${currentPage}: ${timeSpent}ms`);
  });
  
  // Track section views
  const sections = document.querySelectorAll('h2, h3');
  const sectionObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const sectionTitle = entry.target.textContent;
        console.log(`Viewed section: ${sectionTitle}`);
      }
    });
  });
  
  sections.forEach(section => sectionObserver.observe(section));
}

// Initialize analytics if enabled
if (window.gtag || window.dataLayer) {
  trackDocumentationUsage();
}