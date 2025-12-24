<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

onMounted(() => {
  // Auto-redirect to home after 5 seconds
  setTimeout(() => {
    router.push('/')
  }, 5000)
})
</script>

<template>
  <div class="verify-email-page">
    <div class="verify-card">
      <div class="success-icon">✓</div>
      <h1>Email Confirmed!</h1>
      <p>Your email address has been successfully verified.</p>
      <p class="subtitle">You can now use all features of your account.</p>
      
      <div class="actions">
        <router-link to="/" class="btn btn-primary">Go to Home</router-link>
        <router-link to="/login" class="btn btn-secondary">Sign In</router-link>
      </div>
      
      <p class="redirect-message">You will be redirected to home in 5 seconds...</p>
    </div>
  </div>
</template>

<style scoped>
.verify-email-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  padding: 2rem;
}

.verify-card {
  background: white;
  border-radius: 8px;
  padding: 3rem 2rem;
  max-width: 500px;
  width: 100%;
  text-align: center;
  border: 1px solid #ddd;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.success-icon {
  width: 80px;
  height: 80px;
  background: #4caf50;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3rem;
  margin: 0 auto 1.5rem;
  font-weight: bold;
}

.verify-card h1 {
  color: #092E20;
  margin-bottom: 1rem;
  font-size: 2rem;
}

.verify-card p {
  color: #666;
  margin-bottom: 0.75rem;
  font-size: 1.1rem;
  line-height: 1.5;
}

.subtitle {
  color: #999;
  font-size: 0.95rem;
}

.actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin: 2rem 0 1.5rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  font-size: 1rem;
  text-decoration: none;
  transition: all 0.2s;
}

.btn-primary {
  background: #092E20;
  color: white;
}

.btn-primary:hover {
  background: #0a3d2b;
}

.btn-secondary {
  background: white;
  color: #092E20;
  border: 2px solid #092E20;
}

.btn-secondary:hover {
  background: #f5f5f5;
}

.redirect-message {
  color: #999;
  font-size: 0.85rem;
  margin-top: 1rem;
}
</style>
