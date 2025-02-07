// static/components/CurrentTime.js
function updateTime() {
  const timeElement = document.getElementById('currentTime');
  if (timeElement) {
      const now = new Date();
      timeElement.textContent = now.toLocaleTimeString('en-US', { 
          hour: '2-digit', 
          minute: '2-digit', 
          second: '2-digit' 
      });
  }
}

// Update time every second
setInterval(updateTime, 1000);
// Initial update
updateTime();