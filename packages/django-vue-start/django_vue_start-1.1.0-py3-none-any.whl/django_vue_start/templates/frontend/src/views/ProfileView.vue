<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

// Profile form
const username = ref('')
const email = ref('')
const profileSuccess = ref('')
const profileError = ref('')

// Password form
const oldPassword = ref('')
const newPassword1 = ref('')
const newPassword2 = ref('')
const passwordSuccess = ref('')
const passwordError = ref('')

onMounted(() => {
    if (authStore.user) {
        username.value = authStore.user.username || ''
        email.value = authStore.user.email || ''
    }
})

const updateProfile = async () => {
    profileSuccess.value = ''
    profileError.value = ''
    try {
        // Only send fields that changed
        const data = {}
        if (username.value !== authStore.user?.username) {
            data.username = username.value
        }
        if (email.value !== authStore.user?.email) {
            data.email = email.value
        }
        
        if (Object.keys(data).length === 0) {
            profileError.value = 'No changes to save'
            return
        }
        
        await authStore.updateProfile(data)
        profileSuccess.value = 'Profile updated successfully!'
    } catch (err) {
        const data = err.response?.data
        if (typeof data === 'object') {
            profileError.value = Object.entries(data).map(function(entry) { return entry[0] + ': ' + (Array.isArray(entry[1]) ? entry[1].join(', ') : entry[1]); }).join('; ')
        } else {
            profileError.value = 'Failed to update profile'
        }
    }
}

const changePassword = async () => {
    passwordSuccess.value = ''
    passwordError.value = ''
    
    if (newPassword1.value !== newPassword2.value) {
        passwordError.value = 'New passwords do not match'
        return
    }
    
    try {
        await authStore.changePassword({
            old_password: oldPassword.value,
            new_password1: newPassword1.value,
            new_password2: newPassword2.value
        })
        passwordSuccess.value = 'Password changed successfully!'
        oldPassword.value = ''
        newPassword1.value = ''
        newPassword2.value = ''
    } catch (err) {
        const data = err.response?.data
        if (typeof data === 'object') {
            passwordError.value = Object.entries(data).map(function(entry) { return entry[0] + ': ' + (Array.isArray(entry[1]) ? entry[1].join(', ') : entry[1]); }).join('; ')
        } else {
            passwordError.value = 'Failed to change password'
        }
    }
}
</script>

<template>
  <div class="profile-page">
    <h1>Profile</h1>
    
    <!-- Profile Form -->
    <div class="form-section">
      <h2>Edit Profile</h2>
      <p v-if="profileSuccess" class="success">{{ profileSuccess }}</p>
      <p v-if="profileError" class="error">{{ profileError }}</p>
      
      <form @submit.prevent="updateProfile">
        <div class="form-group">
          <label>Username</label>
          <input v-model="username" placeholder="Username" required />
        </div>
        <div class="form-group">
          <label>Email</label>
          <input type="email" v-model="email" placeholder="Email" required />
        </div>
        <button type="submit" class="btn btn-primary" :disabled="authStore.loading">
          {{ authStore.loading ? 'Saving...' : 'Save Changes' }}
        </button>
      </form>
    </div>
    
    <!-- Password Form -->
    <div class="form-section">
      <h2>Change Password</h2>
      <p v-if="passwordSuccess" class="success">{{ passwordSuccess }}</p>
      <p v-if="passwordError" class="error">{{ passwordError }}</p>
      
      <form @submit.prevent="changePassword">
        <div class="form-group">
          <label>Current Password</label>
          <input type="password" v-model="oldPassword" placeholder="Current password" required />
        </div>
        <div class="form-group">
          <label>New Password</label>
          <input type="password" v-model="newPassword1" placeholder="New password" required />
        </div>
        <div class="form-group">
          <label>Confirm New Password</label>
          <input type="password" v-model="newPassword2" placeholder="Confirm new password" required />
        </div>
        <button type="submit" class="btn btn-primary" :disabled="authStore.loading">
          {{ authStore.loading ? 'Changing...' : 'Change Password' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  max-width: 500px;
  margin: 0 auto;
}

.profile-page h1 {
  color: #092E20;
  margin-bottom: 2rem;
}

.form-section {
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.form-section h2 {
  color: #092E20;
  font-size: 1.25rem;
  margin-bottom: 1rem;
}

.success {
  background: #d4edda;
  color: #155724;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.error {
  background: #fee;
  color: #c00;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
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
</style>
