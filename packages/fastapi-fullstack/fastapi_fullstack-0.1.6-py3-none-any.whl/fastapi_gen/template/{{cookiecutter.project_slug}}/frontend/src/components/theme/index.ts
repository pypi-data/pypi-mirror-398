{%- if cookiecutter.use_frontend %}
export { ThemeProvider } from "./theme-provider";
export { ThemeToggle } from "./theme-toggle";
{%- else %}
/* Theme components - frontend not configured */
export {};
{%- endif %}
