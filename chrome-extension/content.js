// Listen for messages from popup
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  if (request.action === "getSelection") {
    sendResponse({selectedText: window.getSelection().toString()});
  }
}); 