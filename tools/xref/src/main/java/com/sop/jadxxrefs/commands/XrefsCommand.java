package com.sop.jadxxrefs.commands;

public class XrefsCommand {
    public static void xrefsToMethod(java.lang.String[] args) throws java.lang.Exception {
        org.apache.commons.cli.Options options = new org.apache.commons.cli.Options();
        options.addOption(org.apache.commons.cli.Option.builder("d").longOpt("jadx-dir").hasArg().required().desc("APK file, or the JADX decompiled directory next to it").build());
        options.addOption(org.apache.commons.cli.Option.builder("c").longOpt("class").hasArg().required().desc("Class name (e.g., com.example.Foo)").build());
        options.addOption(org.apache.commons.cli.Option.builder("m").longOpt("method").hasArg().required().desc("Method name").build());
        org.apache.commons.cli.CommandLine cmd = parseArgs(options, args);
        java.lang.String jadxDir = cmd.getOptionValue("jadx-dir");
        java.lang.String className = cmd.getOptionValue("class");
        java.lang.String methodName = cmd.getOptionValue("method");
        com.sop.jadxxrefs.JadxLoader loader = new com.sop.jadxxrefs.JadxLoader(jadxDir);
        try {
            jadx.api.JavaClass javaClass = loader.findClassByName(className);
            if (javaClass == null) {
                com.sop.jadxxrefs.utils.JsonOutput.printError("Class not found: " + className);
                java.lang.System.exit(1);
            }
            java.util.List<jadx.api.JavaMethod> matchedMethods = findMethodsByName(javaClass, methodName);
            if (matchedMethods.isEmpty()) {
                com.sop.jadxxrefs.utils.JsonOutput.printError("Method not found: " + methodName + " in " + className);
                java.lang.System.exit(1);
            }
            java.util.List<jadx.api.JavaMethod> relatedMethods = new java.util.ArrayList<>();
            for (jadx.api.JavaMethod baseMethod : matchedMethods) {
                for (jadx.api.JavaMethod m : getMethodWithOverrides(baseMethod)) {
                    if (!relatedMethods.contains(m)) {
                        relatedMethods.add(m);
                    }
                }
            }
            java.util.List<jadx.core.dex.nodes.MethodNode> allMethodReferences = new java.util.ArrayList<>();
            for (jadx.api.JavaMethod relatedMethod : relatedMethods) {
                allMethodReferences.addAll(relatedMethod.getMethodNode().getUseIn());
            }
            java.util.List<java.util.Map<java.lang.String, java.lang.String>> referenceList = collectMethodNodeReferences(allMethodReferences);
            com.sop.jadxxrefs.utils.JsonOutput.printXrefs(referenceList);
            loader.close();
        } catch (java.lang.Throwable th) {
            try {
                loader.close();
            } catch (java.lang.Throwable th2) {
                th.addSuppressed(th2);
            }
            throw th;
        }
    }

    public static void xrefsToClass(java.lang.String[] args) throws java.lang.Exception {
        org.apache.commons.cli.Options options = new org.apache.commons.cli.Options();
        options.addOption(org.apache.commons.cli.Option.builder("d").longOpt("jadx-dir").hasArg().required().desc("APK file, or the JADX decompiled directory next to it").build());
        options.addOption(org.apache.commons.cli.Option.builder("c").longOpt("class").hasArg().required().desc("Class name (e.g., com.example.Foo)").build());
        org.apache.commons.cli.CommandLine cmd = parseArgs(options, args);
        java.lang.String jadxDir = cmd.getOptionValue("jadx-dir");
        java.lang.String className = cmd.getOptionValue("class");
        com.sop.jadxxrefs.JadxLoader loader = new com.sop.jadxxrefs.JadxLoader(jadxDir);
        try {
            jadx.api.JavaClass targetClass = loader.findClassByName(className);
            if (targetClass == null) {
                com.sop.jadxxrefs.utils.JsonOutput.printError("Class not found: " + className);
                java.lang.System.exit(1);
            }
            jadx.core.dex.nodes.ClassNode targetClassNode = targetClass.getClassNode();
            java.util.List<jadx.core.dex.nodes.ClassNode> classReferences = targetClassNode.getUseIn();
            java.util.List<jadx.core.dex.nodes.MethodNode> methodReferences = new java.util.ArrayList<>(targetClassNode.getUseInMth());
            for (jadx.api.JavaMethod javaMethod : targetClass.getMethods()) {
                if (javaMethod.isConstructor()) {
                    methodReferences.addAll(javaMethod.getMethodNode().getUseIn());
                }
            }
            java.util.Map<java.lang.String, java.util.Set<java.lang.String>> classToMethodsMap = new java.util.HashMap<>();
            for (jadx.core.dex.nodes.MethodNode mth : methodReferences) {
                jadx.core.dex.nodes.ClassNode parentClass = mth.getParentClass();
                if (parentClass != null) {
                    classToMethodsMap.computeIfAbsent(parentClass.getFullName(), k -> {
                        return new java.util.HashSet();
                    }).add(mth.getName());
                }
            }
            java.util.Set<java.lang.String> existingClassNames = new java.util.HashSet<>();
            for (jadx.core.dex.nodes.ClassNode cls : classReferences) {
                existingClassNames.add(cls.getFullName());
            }
            java.util.Iterator<jadx.core.dex.nodes.MethodNode> it = methodReferences.iterator();
            while (it.hasNext()) {
                jadx.core.dex.nodes.ClassNode parentClass2 = it.next().getParentClass();
                if (parentClass2 != null && !existingClassNames.contains(parentClass2.getFullName())) {
                    classReferences.add(parentClass2);
                    existingClassNames.add(parentClass2.getFullName());
                }
            }
            java.util.List<java.util.Map<java.lang.String, java.lang.String>> referenceList = new java.util.ArrayList<>();
            java.util.Set<java.lang.String> seenReferences = new java.util.HashSet<>();
            for (jadx.core.dex.nodes.ClassNode refClassNode : classReferences) {
                java.lang.String refClassName = refClassNode.getFullName();
                if (classToMethodsMap.containsKey(refClassName)) {
                    for (jadx.core.dex.nodes.MethodNode mth2 : methodReferences) {
                        if (mth2.getParentClass() != null && mth2.getParentClass().getFullName().equals(refClassName)) {
                            addIfUnique(referenceList, seenReferences, extractMethodNodeReferenceInfo(mth2));
                        }
                    }
                } else {
                    java.util.Map<java.lang.String, java.lang.String> refInfo = new java.util.HashMap<>();
                    refInfo.put("class", refClassName);
                    refInfo.put("method", "");
                    addIfUnique(referenceList, seenReferences, refInfo);
                }
            }
            com.sop.jadxxrefs.utils.JsonOutput.printXrefs(referenceList);
            loader.close();
        } catch (java.lang.Throwable th) {
            try {
                loader.close();
            } catch (java.lang.Throwable th2) {
                th.addSuppressed(th2);
            }
            throw th;
        }
    }

    public static void xrefsToField(java.lang.String[] args) throws java.lang.Exception {
        org.apache.commons.cli.Options options = new org.apache.commons.cli.Options();
        options.addOption(org.apache.commons.cli.Option.builder("d").longOpt("jadx-dir").hasArg().required().desc("APK file, or the JADX decompiled directory next to it").build());
        options.addOption(org.apache.commons.cli.Option.builder("c").longOpt("class").hasArg().required().desc("Class name (e.g., com.example.Foo)").build());
        options.addOption(org.apache.commons.cli.Option.builder("f").longOpt("field").hasArg().required().desc("Field name").build());
        org.apache.commons.cli.CommandLine cmd = parseArgs(options, args);
        java.lang.String jadxDir = cmd.getOptionValue("jadx-dir");
        java.lang.String className = cmd.getOptionValue("class");
        java.lang.String fieldName = cmd.getOptionValue("field");
        com.sop.jadxxrefs.JadxLoader loader = new com.sop.jadxxrefs.JadxLoader(jadxDir);
        try {
            jadx.api.JavaClass javaClass = loader.findClassByName(className);
            if (javaClass == null) {
                com.sop.jadxxrefs.utils.JsonOutput.printError("Class not found: " + className);
                java.lang.System.exit(1);
            }
            jadx.api.JavaField targetField = findFieldByName(javaClass, fieldName);
            if (targetField == null) {
                com.sop.jadxxrefs.utils.JsonOutput.printError("Field not found: " + fieldName + " in " + className);
                java.lang.System.exit(1);
            }
            jadx.core.dex.nodes.FieldNode fieldNode = targetField.getFieldNode();
            java.util.List<jadx.core.dex.nodes.MethodNode> fieldReferences = fieldNode.getUseIn();
            java.util.List<java.util.Map<java.lang.String, java.lang.String>> referenceList = collectMethodNodeReferences(fieldReferences);
            com.sop.jadxxrefs.utils.JsonOutput.printXrefs(referenceList);
            loader.close();
        } catch (java.lang.Throwable th) {
            try {
                loader.close();
            } catch (java.lang.Throwable th2) {
                th.addSuppressed(th2);
            }
            throw th;
        }
    }

    private static org.apache.commons.cli.CommandLine parseArgs(org.apache.commons.cli.Options options, java.lang.String[] args) throws java.io.IOException {
        org.apache.commons.cli.CommandLineParser parser = new org.apache.commons.cli.DefaultParser();
        try {
            return parser.parse(options, args);
        } catch (org.apache.commons.cli.ParseException e) {
            java.lang.System.err.println("Error: " + e.getMessage());
            new org.apache.commons.cli.HelpFormatter().printHelp("xrefs-command", options);
            java.lang.System.exit(1);
            return null;
        }
    }

    private static java.util.List<jadx.api.JavaMethod> findMethodsByName(jadx.api.JavaClass javaClass, java.lang.String methodName) {
        java.util.List<jadx.api.JavaMethod> matchedMethods = new java.util.ArrayList<>();
        java.lang.String simpleClassName = javaClass.getName();
        for (jadx.api.JavaMethod method : javaClass.getMethods()) {
            if (!method.isConstructor() && method.getName().equals(methodName)) {
                matchedMethods.add(method);
            } else if (method.isConstructor() && methodName.equals(simpleClassName)) {
                matchedMethods.add(method);
            }
        }
        return matchedMethods;
    }

    private static jadx.api.JavaField findFieldByName(jadx.api.JavaClass javaClass, java.lang.String fieldName) {
        for (jadx.api.JavaField field : javaClass.getFields()) {
            if (field.getName().equals(fieldName)) {
                return field;
            }
        }
        return null;
    }

    private static java.util.List<jadx.api.JavaMethod> getMethodWithOverrides(jadx.api.JavaMethod javaMethod) {
        java.util.List<jadx.api.JavaMethod> related = javaMethod.getOverrideRelatedMethods();
        return (related == null || related.isEmpty()) ? java.util.Collections.singletonList(javaMethod) : related;
    }

    private static java.util.List<java.util.Map<java.lang.String, java.lang.String>> collectMethodNodeReferences(java.util.List<jadx.core.dex.nodes.MethodNode> methodNodes) {
        java.util.Set<java.lang.String> seenReferences = new java.util.HashSet<>();
        java.util.List<java.util.Map<java.lang.String, java.lang.String>> referenceList = new java.util.ArrayList<>();
        for (jadx.core.dex.nodes.MethodNode refMethodNode : methodNodes) {
            java.util.Map<java.lang.String, java.lang.String> refInfo = extractMethodNodeReferenceInfo(refMethodNode);
            addIfUnique(referenceList, seenReferences, refInfo);
        }
        return referenceList;
    }

    private static java.util.Map<java.lang.String, java.lang.String> extractMethodNodeReferenceInfo(jadx.core.dex.nodes.MethodNode methodNode) {
        if (methodNode == null) {
            return null;
        }
        try {
            java.util.Map<java.lang.String, java.lang.String> refInfo = new java.util.HashMap<>();
            jadx.core.dex.nodes.ClassNode parent = methodNode.getParentClass();
            if (parent != null) {
                refInfo.put("class", parent.getFullName());
                java.lang.String outerClass = parent.getFullName().replace('.', '/').split("\\$")[0];
                refInfo.put("file_path", outerClass + ".java");
            }
            jadx.api.JavaMethod javaMethod = methodNode.getJavaNode();
            java.lang.String name = javaMethod != null ? javaMethod.getName() : methodNode.getName();
            if ("<clinit>".equals(name)) {
                name = "";
            }
            refInfo.put("method", name);
            return refInfo;
        } catch (java.lang.Exception e) {
            return null;
        }
    }

    private static void addIfUnique(java.util.List<java.util.Map<java.lang.String, java.lang.String>> list, java.util.Set<java.lang.String> seen, java.util.Map<java.lang.String, java.lang.String> item) {
        if (item != null) {
            java.lang.String key = item.get("class") + "#" + item.get("method");
            if (!seen.contains(key)) {
                seen.add(key);
                list.add(item);
            }
        }
    }

    public static void xrefsToSystemApi(java.lang.String[] args) throws java.lang.Exception {
        java.lang.String strSubstring;
        java.lang.String code = null;
        java.lang.String methodCode = null;
        org.apache.commons.cli.Options options = new org.apache.commons.cli.Options();
        options.addOption(org.apache.commons.cli.Option.builder("d").longOpt("jadx-dir").hasArg().required().desc("APK file, or the JADX decompiled directory next to it").build());
        options.addOption(org.apache.commons.cli.Option.builder("c").longOpt("class").hasArg().required().desc("System class name (e.g., android.telephony.TelephonyManager)").build());
        options.addOption(org.apache.commons.cli.Option.builder("m").longOpt("method").hasArg().desc("Method name (optional; if omitted, searches all references to the class)").build());
        options.addOption(org.apache.commons.cli.Option.builder().longOpt("host-package").hasArg().desc("Host app package prefix for filtering results (e.g., com.example.app)").build());
        org.apache.commons.cli.CommandLine cmd = parseArgs(options, args);
        java.lang.String jadxDir = cmd.getOptionValue("jadx-dir");
        java.lang.String className = cmd.getOptionValue("class");
        java.lang.String methodName = cmd.getOptionValue("method");
        java.lang.String hostPackage = cmd.getOptionValue("host-package", "");
        com.sop.jadxxrefs.JadxLoader loader = new com.sop.jadxxrefs.JadxLoader(jadxDir);
        try {
            java.util.List<java.util.Map<java.lang.String, java.lang.String>> referenceList = new java.util.ArrayList<>();
            jadx.api.JavaClass targetClass = loader.findClassByName(className);
            if (targetClass != null && methodName != null && !methodName.isEmpty()) {
                java.util.List<jadx.api.JavaMethod> matchedMethods = findMethodsByName(targetClass, methodName);
                if (!matchedMethods.isEmpty()) {
                    java.util.List<jadx.api.JavaMethod> relatedMethods = new java.util.ArrayList<>();
                    for (jadx.api.JavaMethod baseMethod : matchedMethods) {
                        for (jadx.api.JavaMethod m : getMethodWithOverrides(baseMethod)) {
                            if (!relatedMethods.contains(m)) {
                                relatedMethods.add(m);
                            }
                        }
                    }
                    java.util.List<jadx.core.dex.nodes.MethodNode> allMethodReferences = new java.util.ArrayList<>();
                    for (jadx.api.JavaMethod relatedMethod : relatedMethods) {
                        allMethodReferences.addAll(relatedMethod.getMethodNode().getUseIn());
                    }
                    referenceList = collectMethodNodeReferences(allMethodReferences);
                }
            } else if (targetClass != null) {
                jadx.core.dex.nodes.ClassNode targetClassNode = targetClass.getClassNode();
                java.util.List<jadx.core.dex.nodes.MethodNode> methodReferences = new java.util.ArrayList<>(targetClassNode.getUseInMth());
                referenceList = collectMethodNodeReferences(methodReferences);
            } else {
                if (className.contains(".")) {
                    strSubstring = className.substring(className.lastIndexOf(46) + 1);
                } else {
                    strSubstring = className;
                }
                java.lang.String simpleClassName = strSubstring;
                for (jadx.api.JavaClass cls : loader.getClasses()) {
                    try {
                        code = cls.getCode();
                    } catch (java.lang.Exception e) {
                    }
                    if (code != null) {
                        boolean classReferenced = code.contains(simpleClassName);
                        if (classReferenced && (methodName == null || methodName.isEmpty() || code.contains(methodName))) {
                            for (jadx.api.JavaMethod method : cls.getMethods()) {
                                try {
                                    methodCode = method.getCodeStr();
                                } catch (java.lang.Exception e2) {
                                }
                                if (methodCode != null && methodCode.contains(simpleClassName) && (methodName == null || methodName.isEmpty() || methodCode.contains(methodName))) {
                                    java.util.Map<java.lang.String, java.lang.String> map = new java.util.HashMap<>();
                                    jadx.core.dex.nodes.ClassNode parent = method.getMethodNode().getParentClass();
                                    if (parent != null) {
                                        map.put("class", parent.getFullName());
                                        java.lang.String outerClass = parent.getFullName().replace('.', '/').split("\\$")[0];
                                        map.put("file_path", outerClass + ".java");
                                    }
                                    map.put("method", method.getName());
                                    map.put("source", "code_scan");
                                    java.lang.String key = map.get("class") + "#" + map.get("method");
                                    if (referenceList.stream().noneMatch(r -> {
                                        return (((java.lang.String) r.get("class")) + "#" + ((java.lang.String) r.get("method"))).equals(key);
                                    })) {
                                        referenceList.add(map);
                                    }
                                }
                            }
                        }
                    }
                }
            }
            if (!hostPackage.isEmpty()) {
                java.lang.String hostPath = hostPackage.replace('.', '/');
                referenceList.removeIf(r2 -> {
                    java.lang.String cls2 = ((java.lang.String) r2.getOrDefault("class", "")).replace('.', '/');
                    return !cls2.startsWith(hostPath);
                });
            }
            java.util.Map<java.lang.String, java.lang.Object> result = new java.util.HashMap<>();
            result.put("query_class", className);
            result.put("query_method", methodName != null ? methodName : "");
            result.put("xrefs", referenceList);
            result.put("count", java.lang.Integer.valueOf(referenceList.size()));
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
    }
}
