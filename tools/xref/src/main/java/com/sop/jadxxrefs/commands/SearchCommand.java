package com.sop.jadxxrefs.commands;

public class SearchCommand {

    /* loaded from: jadx-xrefs-cli.jar:com/sop/jadxxrefs/commands/SearchCommand$SearchLocation.class */
    public enum SearchLocation {
        CLASS_NAME,
        METHOD_NAME,
        FIELD_NAME,
        CODE
    }

    public static void searchClasses(java.lang.String[] args) throws java.lang.Exception {
        org.apache.commons.cli.Options options = new org.apache.commons.cli.Options();
        options.addOption(org.apache.commons.cli.Option.builder("d").longOpt("jadx-dir").hasArg().required().desc("APK file, or the JADX decompiled directory next to it").build());
        options.addOption(org.apache.commons.cli.Option.builder("k").longOpt("keyword").hasArg().required().desc("Search keyword").build());
        options.addOption(org.apache.commons.cli.Option.builder("l").longOpt("location").hasArg().desc("Search location: class_name, method_name, field_name, code (default)").build());
        org.apache.commons.cli.CommandLineParser parser = new org.apache.commons.cli.DefaultParser();
        try {
            org.apache.commons.cli.CommandLine cmd = parser.parse(options, args);
            java.lang.String jadxDir = cmd.getOptionValue("jadx-dir");
            java.lang.String keyword = cmd.getOptionValue("keyword");
            java.lang.String locationStr = cmd.getOptionValue("location", "code");
            com.sop.jadxxrefs.commands.SearchCommand.SearchLocation location = parseSearchLocation(locationStr);
            com.sop.jadxxrefs.JadxLoader loader = new com.sop.jadxxrefs.JadxLoader(jadxDir);
            try {
                java.util.ArrayList arrayList = new java.util.ArrayList();
                for (jadx.api.JavaClass cls : loader.getClasses()) {
                    if (matchKeyword(cls, keyword, location)) {
                        java.util.HashMap map = new java.util.HashMap();
                        map.put("class", cls.getFullName());
                        map.put("match_location", location.name().toLowerCase());
                        arrayList.add(map);
                    }
                }
                java.util.Map<java.lang.String, java.lang.Object> output = new java.util.HashMap<>();
                output.put("keyword", keyword);
                output.put("location", location.name().toLowerCase());
                output.put("results", arrayList);
                output.put("count", java.lang.Integer.valueOf(arrayList.size()));
                com.sop.jadxxrefs.utils.JsonOutput.print(output);
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
            new org.apache.commons.cli.HelpFormatter().printHelp("search-classes", options);
            java.lang.System.exit(1);
        }
    }

    private static com.sop.jadxxrefs.commands.SearchCommand.SearchLocation parseSearchLocation(java.lang.String str) {
        switch (str.toLowerCase()) {
            case "class":
            case "class_name":
                return com.sop.jadxxrefs.commands.SearchCommand.SearchLocation.CLASS_NAME;
            case "method":
            case "method_name":
                return com.sop.jadxxrefs.commands.SearchCommand.SearchLocation.METHOD_NAME;
            case "field":
            case "field_name":
                return com.sop.jadxxrefs.commands.SearchCommand.SearchLocation.FIELD_NAME;
            case "code":
            default:
                return com.sop.jadxxrefs.commands.SearchCommand.SearchLocation.CODE;
        }
    }

    private static boolean matchKeyword(jadx.api.JavaClass cls, java.lang.String keyword, com.sop.jadxxrefs.commands.SearchCommand.SearchLocation location) {
        java.lang.String lowerKeyword = keyword.toLowerCase();
        switch (location) {
            case CLASS_NAME:
                return cls.getFullName().toLowerCase().contains(lowerKeyword);
            case METHOD_NAME:
                for (jadx.api.JavaMethod method : cls.getMethods()) {
                    if (method.getName().toLowerCase().contains(lowerKeyword)) {
                        return true;
                    }
                }
                return false;
            case FIELD_NAME:
                for (jadx.api.JavaField field : cls.getFields()) {
                    if (field.getName().toLowerCase().contains(lowerKeyword)) {
                        return true;
                    }
                }
                return false;
            case CODE:
            default:
                try {
                    java.lang.String code = cls.getCode();
                    if (code != null) {
                        if (code.toLowerCase().contains(lowerKeyword)) {
                            return true;
                        }
                    }
                    return false;
                } catch (java.lang.Exception e) {
                    return false;
                }
        }
    }
}
