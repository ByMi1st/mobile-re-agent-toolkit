package com.sop.jadxxrefs;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.FileDescriptor;
import java.io.FileOutputStream;
import java.io.InputStreamReader;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class Server {
    private static final Gson GSON = new Gson();

    public static int run(String[] args) throws Exception {
        String apk = null;
        for (int i = 0; i + 1 < args.length; i++) {
            if (args[i].equals("-d") || args[i].equals("--jadx-dir")) {
                apk = args[i + 1];
            }
        }
        if (apk == null) {
            System.err.println("serve requires -d APK");
            return 1;
        }
        JadxLoader.shared(apk);
        PrintStream protocol = new PrintStream(new FileOutputStream(FileDescriptor.out), true, StandardCharsets.UTF_8.name());
        BufferedReader input = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
        String line;
        while ((line = input.readLine()) != null) {
            if (line.isBlank()) {
                continue;
            }
            protocol.println(GSON.toJson(handle(line, apk)));
        }
        return 0;
    }

    private static Map<String, Object> handle(String line, String apk) {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        ByteArrayOutputStream err = new ByteArrayOutputStream();
        PrintStream originalOut = System.out;
        PrintStream originalErr = System.err;
        System.setOut(new PrintStream(out, true, StandardCharsets.UTF_8));
        System.setErr(new PrintStream(err, true, StandardCharsets.UTF_8));
        int exit = 0;
        String error = null;
        try {
            List<String> argv = parseArgv(line);
            argv.add(1, "-d");
            argv.add(2, apk);
            Main.dispatch(argv.toArray(new String[0]));
        } catch (CommandException e) {
            exit = 1;
        } catch (Exception e) {
            exit = 1;
            error = String.valueOf(e.getMessage());
        } finally {
            System.setOut(originalOut);
            System.setErr(originalErr);
        }
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("exit", exit);
        response.put("stdout", out.toString(StandardCharsets.UTF_8));
        response.put("stderr", err.toString(StandardCharsets.UTF_8));
        if (error != null) {
            response.put("error", error);
        }
        return response;
    }

    private static List<String> parseArgv(String line) {
        JsonObject request = JsonParser.parseString(line).getAsJsonObject();
        JsonArray array = request.getAsJsonArray("argv");
        if (array == null || array.size() == 0) {
            throw new IllegalArgumentException("request needs a non-empty argv array");
        }
        List<String> argv = new ArrayList<>();
        for (JsonElement element : array) {
            argv.add(element.getAsString());
        }
        for (String arg : argv) {
            if (arg.equals("-d") || arg.equals("--jadx-dir")) {
                throw new IllegalArgumentException("the APK is fixed by the server; do not pass -d");
            }
        }
        return argv;
    }
}
