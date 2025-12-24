<script setup>
import { ref } from 'vue'
import api from '../api/axios'

const email = ref('')
const submitted = ref(false)
const error = ref('')
const loading = ref(false)

const handleSubmit = async () => {
    loading.value = true
    error.value = ''
    try {
        await api.post('/auth/password/reset/', { email: email.value })
        submitted.value = true
    } catch (e) {
        error.value = e.response?.data?.email?.[0] || 'Failed to send reset email'
    } finally {
        loading.value = false
    }
}
</script>

<template>
    <div class="password-reset">
        <h2>Reset Password</h2>
        
        <div v-if="submitted" class="success-message">
            <p>If an account exists with that email, we've sent password reset instructions.</p>
            <router-link to="/login">Back to Login</router-link>
        </div>
        
        <form v-else @submit.prevent="handleSubmit">
            <p>Enter your email address and we'll send you a link to reset your password.</p>
            <input 
                v-model="email" 
                type="email" 
                placeholder="Email address" 
                required 
            />
            <button type="submit" :disabled="loading">
                {{ loading ? 'Sending...' : 'Send Reset Link' }}
            </button>
            <p v-if="error" class="error">{{ error }}</p>
            <router-link to="/login">Back to Login</router-link>
        </form>
    </div>
</template>

<style scoped>
.password-reset {
    max-width: 400px;
    margin: 2rem auto;
    padding: 2rem;
}

.success-message {
    text-align: center;
    padding: 1rem;
    background: #d4edda;
    border-radius: 8px;
}

form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

input {
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
}

button {
    padding: 0.75rem;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
}

button:disabled {
    opacity: 0.7;
    cursor: not-allowed;
}

.error {
    color: #dc3545;
}

a {
    color: #007bff;
    text-decoration: none;
}
</style>
