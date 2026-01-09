import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './style.css'
import { installAppContext } from './context/appContext'

const app = createApp(App)
installAppContext(app)

app.use(router).mount('#app')
