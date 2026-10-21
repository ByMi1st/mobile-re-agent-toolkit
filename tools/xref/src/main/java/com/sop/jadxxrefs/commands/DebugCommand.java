package com.sop.jadxxrefs.commands;

public class DebugCommand {
    public static void listClasses(java.lang.String[] args) throws java.lang.Exception {
        org.apache.commons.cli.Options options = new org.apache.commons.cli.Options();
        options.addOption(org.apache.commons.cli.Option.builder("d").longOpt("jadx-dir").hasArg().required().desc("APK file, or the JADX decompiled directory next to it or APK file").build());
        options.addOption(org.apache.commons.cli.Option.builder("n").longOpt("limit").hasArg().desc("Limit number of classes to show (default: 20)").build());
        org.apache.commons.cli.CommandLineParser parser = new org.apache.commons.cli.DefaultParser();
        try {
            org.apache.commons.cli.CommandLine cmd = parser.parse(options, args);
            java.lang.String jadxDir = cmd.getOptionValue("jadx-dir");
            int limit = java.lang.Integer.parseInt(cmd.getOptionValue("limit", "20"));
            com.sop.jadxxrefs.JadxLoader loader = com.sop.jadxxrefs.JadxLoader.shared(jadxDir);
            try {
                int totalClasses = loader.getClasses().size();
                java.lang.System.err.println("Total classes loaded: " + totalClasses);
                java.util.Map<java.lang.String, java.lang.Object> result = new java.util.HashMap<>();
                result.put("total", java.lang.Integer.valueOf(totalClasses));
                result.put("sample", loader.getClasses().stream().limit(limit).map(cls -> {
                    return cls.getFullName();
                }).toArray());
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
            new org.apache.commons.cli.HelpFormatter().printHelp("debug-list-classes", options);
            throw new com.sop.jadxxrefs.CommandException();
        }
    }
}
