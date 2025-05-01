// Create context menu item
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "summarizeSelection",
    title: "Summarize selected text",
    contexts: ["selection"]
  });
});

// Handle context menu click
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "summarizeSelection") {
    // Open popup with selected text
    chrome.action.openPopup();
  }
}); 