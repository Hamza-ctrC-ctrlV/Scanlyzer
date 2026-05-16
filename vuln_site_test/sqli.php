<?php
// Simple SQLi demo (no real DB, echo demonstrates the vulnerable parameter)
$id = isset($_GET['id']) ? $_GET['id'] : '';
?>
<!doctype html>
<html>
<head><meta charset="utf-8"><title>SQLi Demo</title></head>
<body>
  <h1>SQLi Demo</h1>
  <p>Profile id: <?php echo $id; ?></p>
  <p>Example query executed on server: SELECT * FROM users WHERE id = '<?php echo $id; ?>'</p>
</body>
</html>