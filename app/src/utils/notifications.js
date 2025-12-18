export const showNotification = (message, type = 'info') => {
  const notificationContainer = document.getElementById('notifications')
  if (!notificationContainer) return

  const notification = document.createElement('div')
  notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`
  notification.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `

  notificationContainer.appendChild(notification)

  // Auto remove after 5 seconds
  setTimeout(() => {
    if (notification.parentNode) {
      notification.parentNode.removeChild(notification)
    }
  }, 5000)
}
