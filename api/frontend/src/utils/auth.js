const TOKEN_KEY = 'livinin-token'
const USER_KEY = 'livinin-user'

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function getStoredAuth() {
  const token = localStorage.getItem(TOKEN_KEY)
  const rawUser = localStorage.getItem(USER_KEY)
  return {
    token,
    user: rawUser ? JSON.parse(rawUser) : null
  }
}

export function setStoredAuth(payload) {
  localStorage.setItem(TOKEN_KEY, payload.token)
  localStorage.setItem(USER_KEY, JSON.stringify(payload.user))
}

export function clearStoredAuth() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}
