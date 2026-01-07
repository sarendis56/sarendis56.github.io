function copyBibtex(elementId, buttonElement) {
    // Get the bibtex content
    const bibtexElement = document.getElementById(elementId);
    const bibtexText = bibtexElement.textContent || bibtexElement.innerText;

    // Copy to clipboard
    navigator.clipboard.writeText(bibtexText.trim()).then(function() {
        // Save original text
        const originalText = buttonElement.textContent;

        // Change button text to show success
        buttonElement.textContent = 'Copied!';
        buttonElement.style.backgroundColor = '#28a745';
        buttonElement.style.color = 'white';

        // Reset after 2 seconds
        setTimeout(function() {
            buttonElement.textContent = originalText;
            buttonElement.style.backgroundColor = '';
            buttonElement.style.color = '';
        }, 2000);
    }).catch(function(err) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = bibtexText.trim();
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            document.execCommand('copy');
            // Save original text
            const originalText = buttonElement.textContent;

            // Change button text to show success
            buttonElement.textContent = 'Copied!';
            buttonElement.style.backgroundColor = '#28a745';
            buttonElement.style.color = 'white';

            // Reset after 2 seconds
            setTimeout(function() {
                buttonElement.textContent = originalText;
                buttonElement.style.backgroundColor = '';
                buttonElement.style.color = '';
            }, 2000);
        } catch (err) {
            alert('Failed to copy BibTeX to clipboard. Please copy manually:\n\n' + bibtexText.trim());
        }

        document.body.removeChild(textArea);
    });
}
