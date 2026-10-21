package com.sop.jadxxrefs.commands;

public class SmaliCommand {
    public static void getSmali(java.lang.String[] args) throws java.lang.Exception {
        org.apache.commons.cli.Options options = new org.apache.commons.cli.Options();
        options.addOption(org.apache.commons.cli.Option.builder("d").longOpt("jadx-dir").hasArg().required().desc("APK file, or the JADX decompiled directory next to it").build());
        options.addOption(org.apache.commons.cli.Option.builder("c").longOpt("class").hasArg().required().desc("Class name (e.g., com.example.Foo)").build());
        org.apache.commons.cli.CommandLineParser parser = new org.apache.commons.cli.DefaultParser();
        try {
            org.apache.commons.cli.CommandLine cmd = parser.parse(options, args);
            java.lang.String jadxDir = cmd.getOptionValue("jadx-dir");
            java.lang.String className = cmd.getOptionValue("class");
            com.sop.jadxxrefs.JadxLoader loader = new com.sop.jadxxrefs.JadxLoader(jadxDir);
            try {
                jadx.api.JavaClass javaClass = loader.findClassByName(className);
                if (javaClass == null) {
                    com.sop.jadxxrefs.utils.JsonOutput.printError("Class not found: " + className);
                    java.lang.System.exit(1);
                }
                java.lang.String code = javaClass.getCode();
                java.util.Map<java.lang.String, java.lang.String> result = new java.util.HashMap<>();
                result.put("class", className);
                result.put("code", code != null ? code : "");
                result.put("note", "JADX 1.5.3 returns decompiled Java code instead of Smali");
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
            new org.apache.commons.cli.HelpFormatter().printHelp("get-smali", options);
            java.lang.System.exit(1);
        }
    }
}
