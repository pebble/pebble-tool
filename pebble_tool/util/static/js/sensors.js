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
        var pebble_accel = convert_to_pebble_accel(accel);
        $('.accel-x').text(accel.x.toFixed(2));
        $('.accel-y').text(accel.y.toFixed(2));
        $('.accel-z').text(accel.z.toFixed(2));
        $('.pebble-accel-x').text(pebble_accel[0]);
        $('.pebble-accel-y').text(pebble_accel[1]);
        $('.pebble-accel-z').text(pebble_accel[2]);
    }, 100);
    var updateHeadingText = function(heading) {
        $('.heading').text(Math.round(heading));
        $('.pebble-heading').text(convert_to_pebble_heading(heading));
    };
    var updateCompassOrientation = function(heading) {
        $('.compass').rotate(Math.round(heading));
    };


    var convert_to_pebble_accel = function(accel) {
        return _.map(accel, function(v, k) { return (v / 0.00981).toFixed(0)|0});
    };
    var convert_to_pebble_heading = function(heading) {
        return (65536 - heading * 182.044).toFixed(0)|0;
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
        samples.push(convert_to_pebble_accel(accel));
        updateAccelText(accel);
        send_queued_samples();
    }, 10);
    window.ondeviceorientation = _.throttle(function(e) {
        var heading = e.webkitCompassHeading !== undefined ? e.webkitCompassHeading : e.alpha;
        updateHeadingText(heading);
        if(pebble != null) {
            pebble.emu_set_compass(convert_to_pebble_heading(heading), Compass.Calibrated);
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
