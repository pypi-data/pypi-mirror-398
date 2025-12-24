import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'home',
            component: HomeView
        },
        {
            path: '/login',
            name: 'login',
            component: () => import('../views/LoginView.vue'),
            meta: { guestOnly: true }
        },
        {
            path: '/register',
            name: 'register',
            component: () => import('../views/RegisterView.vue'),
            meta: { guestOnly: true }
        },
        {
            path: '/profile',
            name: 'profile',
            component: () => import('../views/ProfileView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/todos',
            name: 'todos',
            component: () => import('../views/TodosView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/password-reset',
            name: 'password-reset',
            component: () => import('../views/PasswordResetView.vue'),
            meta: { guestOnly: true }
        },
        {
            path: '/password-reset-confirm/:uid/:token',
            name: 'password-reset-confirm',
            component: () => import('../views/PasswordResetConfirmView.vue'),
            meta: { guestOnly: true }
        },
        {
            path: '/auth/verify-email',
            name: 'verify-email',
            component: () => import('../views/VerifyEmailView.vue')
        }
    ]
})

// Track if we've already checked auth status
let authChecked = false

// Navigation Guard
router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore()

    // Only fetch user once on initial page load
    if (!authChecked) {
        authChecked = true
        try {
            await authStore.fetchUser()
        } catch (e) {
            // Not logged in - that's fine
        }
    }

    // Check if route requires authentication
    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
        next({ name: 'login', query: { redirect: to.fullPath } })
        return
    }

    // Redirect authenticated users away from guest-only pages
    if (to.meta.guestOnly && authStore.isAuthenticated) {
        next({ name: 'home' })
        return
    }

    next()
})

export default router
