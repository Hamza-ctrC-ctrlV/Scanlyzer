<?php
// Simple reflected XSS demo
$q = isset($_GET['q']) ? $_GET['q'] : '';
?>
<!doctype html>
<html>
<head><meta charset="utf-8"><title>XSS Demo</title></head>
<body>
  <h1>Reflected XSS Demo</h1>
  <form method="get" action="xss.php">
    <input name="q" value="<?php echo htmlspecialchars($q); ?>" />
    <button type="submit">Search</button>
  </form>
  <p>Results for: <?php echo $q; ?></p> <!-- intentionally vulnerable (no escaping) -->
</body>
</html>