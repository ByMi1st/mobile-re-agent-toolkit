package com.sop.jadxxrefs.commands;

public class InspectCommand {
    public static void inspectClass(java.lang.String[] args) throws java.lang.Exception {
        org.apache.commons.cli.Options options = new org.apache.commons.cli.Options();
        options.addOption(org.apache.commons.cli.Option.builder("d").longOpt("jadx-dir").hasArg().required().desc("APK file, or the JADX decompiled directory next to it").build());
        options.addOption(org.apache.commons.cli.Option.builder("c").longOpt("class").hasArg().required().desc("Class name (e.g., com.example.Foo)").build());
        options.addOption(org.apache.commons.cli.Option.builder().longOpt("show-methods").desc("Show methods (default: true)").build());
        options.addOption(org.apache.commons.cli.Option.builder().longOpt("show-fields").desc("Show fields (default: true)").build());
        org.apache.commons.cli.CommandLineParser parser = new org.apache.commons.cli.DefaultParser();
        try {
            org.apache.commons.cli.CommandLine cmd = parser.parse(options, args);
            java.lang.String jadxDir = cmd.getOptionValue("jadx-dir");
            java.lang.String className = cmd.getOptionValue("class");
            boolean showMethods = cmd.hasOption("show-methods") || !cmd.hasOption("show-fields");
            boolean showFields = cmd.hasOption("show-fields") || !cmd.hasOption("show-methods");
            com.sop.jadxxrefs.JadxLoader loader = com.sop.jadxxrefs.JadxLoader.shared(jadxDir);
            loader.preloadAll();
            try {
                jadx.api.JavaClass javaClass = loader.findClassByName(className);
                if (javaClass == null) {
                    com.sop.jadxxrefs.utils.JsonOutput.printError("Class not found: " + className);
                    throw new com.sop.jadxxrefs.CommandException();
                }
                java.util.Map<java.lang.String, java.lang.Object> result = new java.util.HashMap<>();
                result.put("class", className);
                if (showMethods) {
                    java.util.List<java.util.Map<java.lang.String, java.lang.String>> methods = new java.util.ArrayList<>();
                    for (jadx.api.JavaMethod method : javaClass.getMethods()) {
                        java.util.Map<java.lang.String, java.lang.String> methodInfo = new java.util.HashMap<>();
                        methodInfo.put("name", method.getName());
                        methodInfo.put("access", method.getAccessFlags().toString());
                        methodInfo.put("return_type", method.getReturnType().toString());
                        methodInfo.put("signature", method.getMethodNode().toString());
                        methods.add(methodInfo);
                    }
                    result.put("methods", methods);
                    result.put("method_count", java.lang.Integer.valueOf(methods.size()));
                }
                if (showFields) {
                    java.util.List<java.util.Map<java.lang.String, java.lang.String>> fields = new java.util.ArrayList<>();
                    for (jadx.api.JavaField field : javaClass.getFields()) {
                        java.util.Map<java.lang.String, java.lang.String> fieldInfo = new java.util.HashMap<>();
                        fieldInfo.put("name", field.getName());
                        fieldInfo.put("access", field.getAccessFlags().toString());
                        fieldInfo.put("type", field.getType().toString());
                        fields.add(fieldInfo);
                    }
                    result.put("fields", fields);
                    result.put("field_count", java.lang.Integer.valueOf(fields.size()));
                }
                com.sop.jadxxrefs.utils.JsonOutput.print(result);
                loader.close();
            } catch (java.lang.Throwable th) {
                try {
                    loader.close();
                } catch (java.lang.Throwable th2) {
                    th.addSuppressed(th2);
                }
                throw th;
            }
        } catch (org.apache.commons.cli.ParseException e) {
            java.lang.System.err.println("Error: " + e.getMessage());
            new org.apache.commons.cli.HelpFormatter().printHelp("inspect-class", options);
            throw new com.sop.jadxxrefs.CommandException();
        }
    }
}
