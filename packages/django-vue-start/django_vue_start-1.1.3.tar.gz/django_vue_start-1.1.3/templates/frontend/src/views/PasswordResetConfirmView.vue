<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api/axios'

const route = useRoute()
const router = useRouter()

const password = ref('')
const passwordConfirm = ref('')
const error = ref('')
const loading = ref(false)
const success = ref(false)

const handleSubmit = async () => {
    if (password.value !== passwordConfirm.value) {
        error.value = 'Passwords do not match'
        return
    }

    loading.value = true
    error.value = ''
    
    try {
        await api.post('/auth/password/reset/confirm/', {
            uid: route.params.uid,
            token: route.params.token,
            new_password1: password.value,
            new_password2: passwordConfirm.value
        })
        success.value = true
        setTimeout(() => {
            router.push('/login')
        }, 3000)
    } catch (e) {
        error.value = e.response?.data?.detail || 'Failed to reset password. The link may have expired.'
    } finally {
        loading.value = false
    }
}
</script>

<template>
    <div class="password-reset-confirm">
        <h2>Set New Password</h2>
        
        <div v-if="success" class="success-message">
            <p>Password reset successful! Redirecting to login...</p>
        </div>
        
        <form v-else @submit.prevent="handleSubmit">
            <input 
                v-model="password" 
                type="password" 
                placeholder="New Password" 
                required 
                minlength="8"
            />
            <input 
                v-model="passwordConfirm" 
                type="password" 
                placeholder="Confirm New Password" 
                required 
            />
            <button type="submit" :disabled="loading">
                {{ loading ? 'Resetting...' : 'Reset Password' }}
            </button>
            <p v-if="error" class="error">{{ error }}</p>
        </form>
    </div>
</template>

<style scoped>
.password-reset-confirm {
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
</style>
