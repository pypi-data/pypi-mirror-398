<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const username = ref('')
const email = ref('')
const password = ref('')
const passwordConfirm = ref('')

const handleRegister = async () => {
    if (password.value !== passwordConfirm.value) {
        authStore.error = "Passwords do not match"
        return
    }
    try {
        await authStore.register({ 
            username: username.value, 
            email: email.value, 
            password1: password.value,
            password2: passwordConfirm.value
        })
        router.push('/')
    } catch (e) {
        console.error(e)
    }
}

const formatError = (err) => {
    if (typeof err === 'string') return err
    if (typeof err === 'object') {
        return Object.entries(err).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join('; ')
    }
    return 'An error occurred'
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <h2>Create Account</h2>
      <p v-if="authStore.error" class="error">{{ formatError(authStore.error) }}</p>
      
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label>Username</label>
          <input v-model="username" placeholder="Username" autocomplete="username" required />
        </div>
        <div class="form-group">
          <label>Email</label>
          <input type="email" v-model="email" placeholder="your@email.com" autocomplete="email" required />
        </div>
        <div class="form-group">
          <label>Password</label>
          <input type="password" v-model="password" placeholder="Password" autocomplete="new-password" required />
        </div>
        <div class="form-group">
          <label>Confirm Password</label>
          <input type="password" v-model="passwordConfirm" placeholder="Confirm password" autocomplete="new-password" required />
        </div>
        <button type="submit" class="btn btn-primary" :disabled="authStore.loading">
          {{ authStore.loading ? 'Creating...' : 'Create Account' }}
        </button>
      </form>
      
      <p class="link">Already have an account? <router-link to="/login">Sign In</router-link></p>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  padding-top: 2rem;
}

.auth-card {
  background: white;
  border-radius: 4px;
  padding: 2rem;
  width: 100%;
  max-width: 400px;
  border: 1px solid #ddd;
}

.auth-card h2 {
  color: #092E20;
  margin-bottom: 1.5rem;
  text-align: center;
}

.error {
  background: #fee;
  color: #c00;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  font-size: 0.9rem;
  color: #333;
}

.btn {
  padding: 0.75rem;
  border-radius: 4px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  font-size: 1rem;
}

.btn-primary {
  background: #092E20;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0a3d2b;
}

.btn-primary:disabled {
  opacity: 0.7;
}

.link {
  text-align: center;
  margin-top: 1.5rem;
  color: #666;
}
</style>
