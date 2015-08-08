var Compass = {
    Uncalibrated: 0,
    Calibrating: 1,
    Calibrated: 2
};


var pebble = new PebbleWebSocket(host, port);
var interval_id;
pebble.on('open', function() {
    var samples = [];

    var updateAccelText = _.throttle(function(accel) {
        $('.accel-x').text(accel.x.toFixed(2));
        $('.accel-y').text(accel.y.toFixed(2));
        $('.accel-z').text(accel.z.toFixed(2));
    }, 100);
    var updateHeadingText = function(heading) {
        $('.heading').text(Math.round(heading));
    };
    var send_queued_samples = _.throttle(function() {
        if(pebble != null) {
            pebble.emu_set_accel(samples);
        }
        samples = [];
    }, 200);

    var isReversed = /Android/i.test(navigator.userAgent);
    window.ondevicemotion = _.throttle(function(e) {
        var accel = _.clone(e.accelerationIncludingGravity);
        if(isReversed) {
            accel.x = -accel.x;
            accel.y = -accel.y;
            accel.z = -accel.z;
        }
        samples.push([accel.x, accel.y, accel.z]);
        updateAccelText(accel);
        send_queued_samples();
    }, 10);
    window.ondeviceorientation = _.throttle(function(e) {
        var heading = e.webkitCompassHeading !== undefined ? e.webkitCompassHeading : e.alpha;
        updateHeadingText(heading);
        if(pebble != null) {
            pebble.emu_set_compass(heading, Compass.Calibrated);
        }
    }, 500);

    if(window.DeviceMotionEvent && window.DeviceOrientationEvent) {
        $('.state').text("(Transmitting)");
        $('.stuff').show();
    } else {
        $('.state').text("Not Supported");
    }
});

pebble.on('close', function() {
    window.ondevicemotion = null;
    window.ondeviceorientation = null;
    $('.state').text("Disconnected");
    $('.stuff').hide();
    pebble = null;
});
