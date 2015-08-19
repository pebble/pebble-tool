SENSOR_PAGE_HTML = """
<html>
    <head>
        <title>Pebble Emulator Control</title>
        <meta name="viewport" content="width=device-width,initial-scale=1,max-scale=1">
        <link rel="icon" href="data:;base64,iVBORw0KGgo=">
        <link rel="stylesheet" type="text/css" href="static/stylesheets/normalize.min.css">
        <link rel="stylesheet" type="text/css" href="static/stylesheets/sensors.css">
        <script src="static/js/underscore-min.js" type="text/javascript"></script>
        <script src="static/js/backbone-min.js" type="text/javascript"></script>
        <script src="static/js/propeller.min.js" type="text/javascript"></script>
        <script type="text/javascript">var host = {websocket_host}; var port = {websocket_port};</script>
        <script src="static/js/websocket.js" type="text/javascript"></script>
        <script src="static/js/sensors.js" type="text/javascript"></script>
    </head>
    <body>
        <div id="state">Connecting</div>
        <h1>Pebble Emulator Control</h1>
        <div id="stuff" style="display: none;">
            <label for="use_sensors">
                <span>Use built-in sensors?</span>
                <input type="checkbox" class="use_sensors" checked id="use_sensors">
            </label>
            <div id="compass-container">
                <div id="compass-text"><span id="pebble-heading">NaN</span> (<span id="heading">NaN</span>&deg;)</div>
                <div id="compass">
                    <img src="static/compass-arrow.png" id="arrow">
                    <img src="static/compass-rose.png" id="compass-bg">
                </div>
            </div>
            <div id="accel">
                <div class="accel-text"><span id="pebble-accel-x">0</span> (<span id="accel-x">0</span>  m/s<sup>2</sup>)</div>
                -x <input id="accel-x-slider" type="range" min="-4000" max="4000" step="1" value="0" /> +x
                <div class="accel-text"><span id="pebble-accel-y">0</span> (<span id="accel-y">0</span>  m/s<sup>2</sup>)</div>
                -y <input id="accel-y-slider" type="range" min="-4000" max="4000" step="1" value="0" /> +y
                <div class="accel-text"><span id="pebble-accel-z">0</span> (<span id="accel-z">0</span>  m/s<sup>2</sup>)</div>
                -z <input id="accel-z-slider" type="range" min="-4000" max="4000" step="1" value="0" /> +z
            </div>
        </div>
    </body>
</html>
"""
