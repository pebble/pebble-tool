var QemuProtocol = {
    Compass: 4,
    Accel: 6
}

var pack = function(format, data) {
    var pointer = 0;
    var bytes = [];
    for(var i = 0; i < format.length; ++i) {
        if(pointer >= data.length) {
            throw new Error("Expected more data.");
        }
        var chr = format.charAt(i);
        switch(chr) {
        case "b":
        case "B":
            bytes.push(data[pointer++]);
            break;
        case "h":
        case "H":
            bytes.push((data[pointer] >> 8) & 0xFF);
            bytes.push(data[pointer] & 0xFF);
            ++pointer;
            break;
        case "l":
        case "L":
        case "i":
        case "I":
            bytes.push((data[pointer] >> 24) & 0xFF);
            bytes.push((data[pointer] >> 16) & 0xFF);
            bytes.push((data[pointer] >> 8) & 0xFF);
            bytes.push(data[pointer] & 0xFF);
            ++pointer;
            break;
        default:
            console.log("Not implemented");
        }
    }
    return bytes;
};


var PebbleWebSocket = function(ip, port) {
    var self = this;
    var mIP = ip;
    var mPort = port;
    var mSocket = null;
    var interval_id = null;

    _.extend(this, Backbone.Events)

    var init = function() {
        mSocket = new WebSocket('ws://' + mIP + ':' + mPort + '/');
        mSocket.binaryType = "arraybuffer";
        mSocket.onerror = handle_socket_error;
        mSocket.onerror = handle_socket_close;
        mSocket.onclose = handle_socket_close;
        mSocket.onmessage = handle_socket_message;
        mSocket.onopen = handle_socket_open;
    };

    this.close = function() {
        if(mSocket != null) {
            mSocket.close();
        }
    };

    this.send = function(data) {
        if(mSocket != null) {
            mSocket.send(data);
        }
    };

    this.send_qemu_message = function(protocol, message) {
        self.send(new Uint8Array([0xb, protocol].concat(message)));
    }

    this.emu_set_compass = function(heading, calibration) {
        data = pack("Ib", [heading, calibration])
        self.send_qemu_message(QemuProtocol.Compass, data);
    };

    this.emu_set_accel = function(samples) {
        var message = [samples.length];
        _.each(samples, function(sample) {
            message = message.concat(pack("hhh", sample ));
        });
        self.send_qemu_message(QemuProtocol.Accel, message);
    };

    this.isOpen = function() {
        return (mSocket.readyState == WebSocket.OPEN);
    };

    var handle_socket_error = function(e) {
        self.trigger('error', e);
    };

    var handle_socket_open = function() {
        console.log("WS Connection Established");
        interval_id = setInterval(function() {
            var request = new XMLHttpRequest();
            request.open('HEAD', 'http://' + location.hostname + ':' + location.port, true);
            request.onerror = function() {
                pebble.close();
            }
            request.send(null);
        }, 2000);
        self.trigger('open');
    };

    var handle_socket_close = function(e) {
        console.log("WS Connection Closed");
        clearInterval(interval_id);
        self.trigger('close', e);
        mSocket = null;
    };

    var handle_socket_message = function(e) {
        self.trigger('message', e.data);
    };

    init();
};
