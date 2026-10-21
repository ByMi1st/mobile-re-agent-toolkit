package com.sop.jadxxrefs.utils;

public class JsonOutput {
    private static final com.google.gson.Gson gson = new com.google.gson.GsonBuilder().setPrettyPrinting().create();

    public static void print(java.lang.Object data) {
        java.lang.System.out.println(gson.toJson(data));
    }

    public static void printError(java.lang.String message) {
        java.util.Map<java.lang.String, java.lang.String> error = new java.util.HashMap<>();
        error.put("error", message);
        java.lang.System.err.println(gson.toJson(error));
    }

    public static void printXrefs(java.util.List<java.util.Map<java.lang.String, java.lang.String>> xrefs) {
        java.util.Map<java.lang.String, java.lang.Object> result = new java.util.HashMap<>();
        result.put("xrefs", xrefs);
        result.put("count", java.lang.Integer.valueOf(xrefs.size()));
        print(result);
    }
}
