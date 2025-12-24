<script setup>
</script>

<template>
  <footer class="app-footer">
    <div class="footer-container">
      <div class="footer-links">
        <a href="https://github.com/abdullafajal/django-vue-start/blob/main/docs/user_guide.md" target="_blank">Quick Start</a>
        <span class="separator">|</span>
        <a href="http://localhost:8000/api/schema/swagger-ui/" target="_blank">API Docs</a>
        <span class="separator">|</span>
        <a href="https://github.com/abdullafajal/django-vue-start" target="_blank">GitHub</a>
      </div>
      <p class="copyright">Built with Django + Vue.js</p>
    </div>
  </footer>
</template>

<style scoped>
.app-footer {
  background: #f5f5f5;
  border-top: 1px solid #ddd;
  padding: 1.5rem 2rem;
  margin-top: auto;
}

.footer-container {
  max-width: 1200px;
  margin: 0 auto;
  text-align: center;
}

.footer-links {
  margin-bottom: 0.5rem;
}

.footer-links a {
  color: #092E20;
  text-decoration: none;
}

.footer-links a:hover {
  text-decoration: underline;
}

.separator {
  margin: 0 0.75rem;
  color: #999;
}

.copyright {
  color: #666;
  font-size: 0.875rem;
}
</style>
