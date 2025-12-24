import { defineStore } from 'pinia'
import api from '../api/axios'

export const useAuthStore = defineStore('auth', {
    state: () => ({
        user: null,
        isAuthenticated: false,
        loading: false,
        error: null
    }),

    actions: {
        async login(credentials) {
            this.loading = true
            this.error = null
            try {
                await api.post('/auth/login/', credentials)
                await this.fetchUser()
            } catch (err) {
                const data = err.response?.data
                if (data?.non_field_errors) {
                    this.error = data.non_field_errors[0]
                } else if (data?.detail) {
                    this.error = data.detail
                } else if (typeof data === 'object') {
                    this.error = Object.values(data).flat().join(', ')
                } else {
                    this.error = 'Login failed'
                }
                throw err
            } finally {
                this.loading = false
            }
        },

        async register(userData) {
            this.loading = true
            this.error = null
            try {
                const response = await api.post('/auth/registration/', userData)
                // Use the user data from registration response instead of fetching again
                this.user = response.data.user
                this.isAuthenticated = true
            } catch (err) {
                this.error = err.response?.data || 'Registration failed'
                throw err
            } finally {
                this.loading = false
            }
        },

        async logout() {
            try {
                await api.post('/auth/logout/')
            } finally {
                this.user = null
                this.isAuthenticated = false
            }
        },

        async fetchUser() {
            try {
                const response = await api.get('/auth/user/')
                this.user = response.data
                this.isAuthenticated = true
            } catch (err) {
                this.user = null
                this.isAuthenticated = false
            }
        },

        async updateProfile(data) {
            this.loading = true
            this.error = null
            try {
                const response = await api.patch('/auth/user/', data)
                this.user = response.data
                return response.data
            } catch (err) {
                this.error = err.response?.data || 'Update failed'
                throw err
            } finally {
                this.loading = false
            }
        },

        async changePassword(data) {
            this.loading = true
            this.error = null
            try {
                await api.post('/auth/password/change/', data)
            } catch (err) {
                this.error = err.response?.data || 'Password change failed'
                throw err
            } finally {
                this.loading = false
            }
        }
    }
})
