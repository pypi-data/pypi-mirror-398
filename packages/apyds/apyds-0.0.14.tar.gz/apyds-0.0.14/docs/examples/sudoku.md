# Sudoku

This example demonstrates a **Sudoku Solver** powered by the DS deductive system. The solver uses logical rules to deduce cell values based on standard Sudoku constraints:

- **Row constraint**: Each row must contain the digits 1-9 exactly once
- **Column constraint**: Each column must contain the digits 1-9 exactly once
- **Box constraint**: Each 3×3 box must contain the digits 1-9 exactly once

## How It Works

The Sudoku solver encodes Sudoku rules as logical inference rules in the DS system. When you click "Solve", the search engine iteratively applies these rules to deduce new cell values until the puzzle is complete. You can also click "Update" to perform a single iteration of inference and observe the step-by-step solving process in the log.

## Interactive Demo

<div id="app">
  <p style="text-align: center; padding: 40px; color: #666; font-style: italic;">
    Loading Sudoku Solver...
  </p>
</div>
<script src="https://unpkg.com/ejs@3.1.10/ejs.min.js"></script>
<script>
(async () => {
  const vue = await import("https://unpkg.com/vue@3.5.25/dist/vue.esm-browser.prod.js");
  const atsds = await import("https://unpkg.com/atsds@0.0.5/dist/index.mjs");
  const { loadModule } = await import("https://unpkg.com/vue3-sfc-loader@0.9.5/dist/vue3-sfc-loader.esm.js");

  const options = {
    moduleCache: { vue, atsds, ejs: window.ejs },
    async getFile(url) {
      const response = await fetch(url);
      return response.text();
    },
    addStyle(css) {
      const style = document.createElement('style');
      style.textContent = css;
      document.head.appendChild(style);
    }
  };

  const Sudoku = await loadModule('./Sudoku.vue', options)
  vue.createApp(Sudoku).mount('#app');
})();
</script>
