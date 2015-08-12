SENSOR_PAGE_HTML = """
<html>
    <head>
        <title>Pebble Emulator Control</title>
        <meta name="viewport" content="width=device-width,initial-scale=1,max-scale=1">
        <link rel="stylesheet" type="text/css" href="static/stylesheets/normalize.min.css">
        <link rel="stylesheet" type="text/css" href="static/stylesheets/sensors.css">
        <script src="static/js/textdecoder.js" type="text/javascript"></script>
        <script src="static/js/jquery-2.1.4.min.js" type="text/javascript"></script>
        <script src="static/js/underscore-min.js" type="text/javascript"></script>
        <script src="static/js/backbone-min.js" type="text/javascript"></script>
        <script src="static/js/jQueryRotate.js" type="text/javascript"></script>
        <script type="text/javascript">var host = {websocket_host}; var port = {websocket_port};</script>
        <script src="static/js/websocket.js" type="text/javascript"></script>
        <script src="static/js/sensors.js" type="text/javascript"></script>
    </head>
    <body>
        <div class="state">Connecting</div>
        <h1>Pebble Emulator Control</h1>
        <div class="stuff" style="display: none;">
            <label for="use_sensors">
              <span>Use built-in sensors?</span>
              <input type="checkbox" class="use_sensors" checked id="use_sensors">
            </label>
            <div class="compass-container">
                <div class="compass-text"><span class="pebble-heading">NaN</span> (<span class="heading">NaN</span>&deg;)</div>
                <div class="compass">
                    <img src="static/compass-rose.png" class="compass-bg">
                    <img src="static/compass-needle.png" class="needle">
                </div>
            </div>
            <div class="accel">
                <div class="accel-text"><span class="pebble-accel-x">0</span> (<span class="accel-x">0</span>  m/s<sup>2</sup>)</div>
                -x <input class="accel-x-slider" type="range" min="-4000" max="4000" step="1" value="0" /> +x
                <div class="accel-text"><span class="pebble-accel-y">0</span> (<span class="accel-y">0</span>  m/s<sup>2</sup>)</div>
                -y <input class="accel-y-slider" type="range" min="-4000" max="4000" step="1" value="0" /> +y
                <div class="accel-text"><span class="pebble-accel-z">0</span> (<span class="accel-z">0</span>  m/s<sup>2</sup>)</div>
                -z <input class="accel-z-slider" type="range" min="-4000" max="4000" step="1" value="0" /> +z
            </div>
        </div>
    </body>
</html>
"""
