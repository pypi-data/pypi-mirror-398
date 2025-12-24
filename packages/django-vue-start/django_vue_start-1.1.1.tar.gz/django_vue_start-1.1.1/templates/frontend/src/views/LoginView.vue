<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter, useRoute } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')

const handleLogin = async () => {
    try {
        await authStore.login({ 
            username: username.value, 
            password: password.value 
        })
        const redirect = route.query.redirect || '/'
        router.push(redirect)
    } catch (e) {
        console.error(e)
    }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <h2>Sign In</h2>
      <p v-if="authStore.error" class="error">{{ authStore.error }}</p>
      
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>Username</label>
          <input v-model="username" placeholder="Username" autocomplete="username" required />
        </div>
        <div class="form-group">
          <label>Password</label>
          <input type="password" v-model="password" placeholder="Password" autocomplete="current-password" required />
        </div>
        <button type="submit" class="btn btn-primary" :disabled="authStore.loading">
          {{ authStore.loading ? 'Signing in...' : 'Sign In' }}
        </button>
      </form>
      
      <p class="link">Don't have an account? <router-link to="/register">Sign Up</router-link></p>
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
