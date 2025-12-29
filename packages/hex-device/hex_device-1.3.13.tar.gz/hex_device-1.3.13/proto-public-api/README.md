# proto-public-api

[English](README.md) | [中文](README_cn.md)

This repository provides the API protocol for most Hexfellow bots. The API uses the WebSocket protocol, with data encoded using Google Protobuf. WebSocket and Protobuf are widely used globally and have support libraries for almost every language. Therefore, you can always choose your preferred language to use this API. Google's official website offers tutorials/reference guides for languages including, but not limited to, Python, C++, Rust, C#, Go, Dart, Kotlin, Objective-C, and Ruby. If you are unsure how to use Protobuf, please refer to tutorials from Google and others.

WebSocket is widely used across various fields worldwide, so it won't be elaborated on here. However, note that our connection only allows sending Binary messages; Text messages will be considered errors. All messages from the bots are of type `APIUp`, and all messages sent to the bots are of type `APIDown`. You should first review `public_api_up.proto` and `public_api_down.proto` to start understanding the communication method of this API.

Unless otherwise specified, the WebSocket service runs on port 8439.

Please note that you need to set TCP_NODELAY and TCP_QUICKACK to get the best performance.

# Advanced Reading

Please note that the following features are advanced features. Unless specifically stated, we **do not provide** any explanation or technical support for these features. If you do not have enough knowledge, please do not use these features.


## PTP Time Synchronization

> This section is for advanced readers. If you don't have enough knowledge, please do not use time synchronization. We also **do not provide** any explanation or technical support for time synchronization.

The system allows using PTP (IEEE 1588) to achieve high-precision sub-millisecond time synchronization.

All main controllers will only be Slave, DOMAIN will be 0.

If you want to use PTP, it is recommended to use a network card with hardware timestamps. See the part of `System Requirements` in `https://linuxptp.sourceforge.net/` for more information.

e.g.
```bash
sudo ptp4l -i enp3s0 -A -m -q
```

You can check if the time synchronization is successful by using the `pmc` command. For example, `pmc -u 'GET PORT_DATA_SET'` to view the current status of each `portIdentity`. The `portIdentity` is usually related to the MAC address of the network card. When all main controllers' statuses change to `SLAVE`, it means the time synchronization is successful.

## KCP Connection

> This section is for advanced readers. If you don't have enough knowledge, please use WebSocket connection.
> 
> If you don't have TCP communication issues, there is no need to switch to KCP connection. And you don't need to read the rest of this section.

To avoid the hassle of adjusting various TCP parameters, further reduce latency and jitter, KCP connection option is added. Before using KCP, you must use WebSocket connection for handshake. The conv id will be equal to the session id in APIUp.

Both the KCP stream up and down need to unpack the Protobuf message and then process it. The header is currently fixed at 4 bytes.

Byte[0] is `0x80 | (opcode as u8);`

Byte[1] is currently fixed at 0

Byte[2] and [3] are the little-endian length of the data

Provide a reference function for creating the header in Rust. If you need more information, please refer to the part of `HexSocketParser` in `https://github.com/hexfellow/kcp-bindings`.

```rust
    #[derive(Debug, Eq, PartialEq)]
    pub enum HexSocketOpcode {
        Text = 0x1,
        Binary = 0x2,
        Ping = 0x9,
        Pong = 0xA,
    }

    pub fn create_header(data: &[u8], opcode: HexSocketOpcode) -> Vec<u8> {
        let len = data.len();
        if len > UINT16_MAX as usize {
            panic!("Data is more than UINT16_MAX bytes");
        }
        let len = len as u16;
        let mut header = [0u8; 4];
        header[0] = 0x80 | (opcode as u8);
        header[1] = 0x00;
        let len = len.to_le_bytes();
        header[2..4].copy_from_slice(&len);
        header.to_vec()
    }
```

Also, refer to the suggestion in https://github.com/skywind3000/kcp/wiki/Cooperate-With-Tcp-Server, if the WebSocket connection is disconnected, the KCP connection will also be considered disconnected.

The handshake process is as follows:
1. Connect to the WebSocket, and get the session id from the WebSocket. Then send the APIDown.EnableKcp message. The client_peer_port in EnableKcp should be the port of the Socket used by the Client. The kcp_config should use the default value provided in the comments.
2. Wait for the kcp_config in APIUp. Get the KCP connection port from the kcp_config.
3. Send an APIDown message from the KCP to notify the Server that the data can be sent.
4. Change the report frequency of the WebSocket to Rf1Hz. (Optional but strongly recommended, because the WebSocket connection is not useful after this, and is only used to keep the KCP connection alive)
5. You can now communicate normally. Note that you can still get data from the WebSocket at this time, and the KCP and WebSocket of the same session id will have the same session id, which means the control is shared.
