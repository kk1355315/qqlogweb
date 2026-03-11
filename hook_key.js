/*
 * hook_key.js
 * 基于 Frida 的 NTQQ 数据库密钥提取脚本
 * 适配: Python 通信版 (使用 send() 发回数据)
 */

var key_found = false;

function report_key(key, dbName, len, method, moduleName) {
    if (key_found) return;
    
    // 发送消息给 Python
    send({
        type: 'key',
        key: key,
        db_name: dbName,
        length: len,
        method: method,
        module_name: moduleName
    });
    
    key_found = true;
}

function hook_sqlite3_key_v2(address, moduleName, method) {
    // send({type: 'log', content: "[+] Try Hook " + method + " @ " + address});
    try {
        Interceptor.attach(address, {
            onEnter: function(args) {
                if (key_found) return;

                var dbName = "unknown";
                try {
                    if (!args[1].isNull()) {
                        dbName = args[1].readUtf8String();
                    }
                } catch (e) {}

                var len = args[3].toInt32();
                if (len > 0) {
                    var key = args[2].readUtf8String(len);
                    if (len >= 16) {
                        report_key(key, dbName, len, method, moduleName);
                    }
                }
            }
        });
    } catch (e) {
        // send({type: 'error', content: "[-] Hook Failed: " + e});
    }
}

function scan_imports_exports() {
    // send({type: 'log', content: "[*] Scanning exports..."});
    var modules = Process.enumerateModules();
    var target_export = "sqlite3_key_v2";
    var count = 0;

    for (var i = 0; i < modules.length; i++) {
        var m = modules[i];
        var name = m.name.toLowerCase();
        
        if (name.indexOf("wrapper") !== -1 || 
            name.indexOf("qq") !== -1 || 
            name.indexOf("sqlite") !== -1) {
            
            var export_addr = Module.findExportByName(m.name, target_export);
            if (export_addr) {
                hook_sqlite3_key_v2(export_addr, m.name, "Export");
                count++;
            }
        }
    }
    return count;
}

function scan_pattern() {
    // send({type: 'log', content: "[*] Export not found. Trying Pattern Scan..."});
    
    var modules = Process.enumerateModules();
    var target_module = null;
    
    for (var i = 0; i < modules.length; i++) {
        if (modules[i].name.toLowerCase().indexOf("wrapper.node") !== -1) {
            target_module = modules[i];
            break;
        }
    }

    if (!target_module) {
        target_module = Process.getModuleByName("QQ.exe");
    }

    if (!target_module) {
        send({type: 'error', content: "[-] Target module not found."});
        return;
    }

    // Pattern for sqlite3_key_v2 (x64 prologue)
    var pattern = "48 89 5C 24 08 48 89 6C 24 10 48 89 74 24 18 57 48 83 EC 20 41 8B F9";
    
    var matches = Memory.scanSync(target_module.base, target_module.size, pattern);
    
    if (matches.length > 0) {
        // send({type: 'log', content: "[+] Found " + matches.length + " candidates. Hooking all..."});
        for (var i = 0; i < matches.length; i++) {
            hook_sqlite3_key_v2(matches[i].address, target_module.name, "Pattern");
        }
    } else {
        send({type: 'error', content: "[-] Pattern not found."});
    }
}

function main() {
    if (scan_imports_exports() === 0) {
        scan_pattern();
    } else {
        // send({type: 'log', content: "[*] Hook Ready (Export)."});
    }
}

setImmediate(main);