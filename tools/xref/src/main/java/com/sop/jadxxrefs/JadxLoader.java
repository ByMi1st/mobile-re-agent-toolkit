package com.sop.jadxxrefs;

public class JadxLoader implements java.lang.AutoCloseable {
    private final jadx.api.JadxDecompiler decompiler;
    private final java.util.List<jadx.api.JavaClass> classes;

    public JadxLoader(java.lang.String jadxDir) throws java.lang.Exception {
        java.io.File inputFile = findInputFile(jadxDir);
        jadx.api.JadxArgs args = new jadx.api.JadxArgs();
        args.setInputFile(inputFile);
        args.setSkipResources(true);
        args.setSkipSources(false);
        args.setDeobfuscationOn(false);
        args.setShowInconsistentCode(true);
        args.setThreadsCount(1);
        this.decompiler = new jadx.api.JadxDecompiler(args);
        java.lang.System.err.println("DEBUG: Loading APK: " + inputFile.getAbsolutePath());
        this.decompiler.load();
        java.lang.System.err.println("DEBUG: Building cross-reference index...");
        for (jadx.api.JavaClass cls : this.decompiler.getClasses()) {
            try {
                cls.getCode();
            } catch (java.lang.Exception e) {
            }
        }
        this.classes = this.decompiler.getClassesWithInners();
        java.lang.System.err.println("DEBUG: Loaded " + this.classes.size() + " classes from " + inputFile.getName());
    }

    private java.io.File findInputFile(java.lang.String jadxDir) throws java.lang.Exception {
        java.io.File parentDir;
        java.io.File dir = new java.io.File(jadxDir);
        if (dir.isFile() && dir.getName().endsWith(".apk")) {
            return dir;
        }
        if (dir.isDirectory() && (parentDir = dir.getParentFile()) != null) {
            java.lang.String dirName = dir.getName();
            java.lang.String baseName = dirName.replace("_decompiled", "").replace("-decompiled", "");
            java.io.File apkFile = new java.io.File(parentDir, baseName + ".apk");
            if (apkFile.exists()) {
                java.lang.System.err.println("INFO: Found APK file: " + apkFile.getAbsolutePath());
                return apkFile;
            }
            java.io.File[] apks = parentDir.listFiles((d, name) -> {
                return name.endsWith(".apk");
            });
            if (apks != null && apks.length > 0) {
                java.lang.System.err.println("INFO: Found APK file: " + apks[0].getAbsolutePath());
                return apks[0];
            }
        }
        throw new java.lang.IllegalArgumentException("Cannot find APK file for: " + jadxDir);
    }

    public java.util.List<jadx.api.JavaClass> getClasses() {
        return this.classes;
    }

    public jadx.api.JavaClass findClassByName(java.lang.String className) {
        for (jadx.api.JavaClass cls : this.classes) {
            if (cls.getFullName().equals(className)) {
                return cls;
            }
        }
        return null;
    }

    @Override // java.lang.AutoCloseable
    public void close() {
        if (this.decompiler != null) {
            this.decompiler.close();
        }
    }
}
