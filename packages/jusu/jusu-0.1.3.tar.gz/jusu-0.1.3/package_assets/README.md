jusu-assets
===========

A minimal, optional npm package for JUSU containing small CSS and JS helpers.

Author: Francis Jusu <jusufrancis08@gmail.com>

Install
-------

```bash
npm install jusu-assets
```

Usage
-----

- CSS: include `package_assets/css/jusu.css` in your HTML or bundler. Example:

```html
<link rel="stylesheet" href="node_modules/jusu-assets/package_assets/css/jusu.css">
```

- JS (ES module): import the helper(s) or include as a module script. Example:

```html
<script type="module">
  import { toggleClass } from '/node_modules/jusu-assets/package_assets/js/jusu.js';
  // usage: toggleClass(el, 'hidden')
</script>
```

Notes
-----
- This package contains **optional** helpers only. The main JUSU functionality is the Python library; the npm package provides convenience assets for simple client-side interactivity or styling.
- The package is intentionally small to avoid heavy JS dependencies.

License: MIT
