document.addEventListener('DOMContentLoaded', function() {
  // Get selected text from the page when popup opens
  chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
    chrome.tabs.sendMessage(tabs[0].id, {action: "getSelection"}, function(response) {
      if (response && response.selectedText) {
        document.getElementById('input').value = response.selectedText;
      }
    });
  });

  // Handle summarize button click
  document.getElementById('summarize').addEventListener('click', function() {
    const text = document.getElementById('input').value;
    if (!text) {
      alert('Please enter some text to summarize');
      return;
    }

    const loading = document.querySelector('.loading');
    const summary = document.getElementById('summary');
    loading.style.display = 'block';
    summary.style.display = 'none';

    // Call our summarization API
    fetch('http://localhost:5000/summarize', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: text,
        algorithm: 'textrank',
        num_sentences: 3
      })
    })
    .then(response => response.json())
    .then(data => {
      loading.style.display = 'none';
      summary.style.display = 'block';
      summary.textContent = data.summary;
    })
    .catch(error => {
      loading.style.display = 'none';
      alert('Error: Could not generate summary. Please try again.');
      console.error('Error:', error);
    });
  });
}); 