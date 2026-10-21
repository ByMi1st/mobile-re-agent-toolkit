package com.sop.jadxxrefs;

import java.util.Arrays;

public class Main {
    public static void main(String[] args) {
        if (args.length == 0) {
            printUsage();
            System.exit(1);
        }
        if (args[0].equals("serve")) {
            try {
                System.exit(Server.run(Arrays.copyOfRange(args, 1, args.length)));
            } catch (Exception e) {
                System.err.println("Error: " + e.getMessage());
                System.exit(1);
            }
        }
        try {
            dispatch(args);
        } catch (CommandException e) {
            System.exit(1);
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }

    static void dispatch(String[] args) throws Exception {
        String command = args[0];
        String[] cmdArgs = Arrays.copyOfRange(args, 1, args.length);
        switch (command) {
            case "xrefs-to-method":
                com.sop.jadxxrefs.commands.XrefsCommand.xrefsToMethod(cmdArgs);
                break;
            case "xrefs-to-class":
                com.sop.jadxxrefs.commands.XrefsCommand.xrefsToClass(cmdArgs);
                break;
            case "xrefs-to-field":
                com.sop.jadxxrefs.commands.XrefsCommand.xrefsToField(cmdArgs);
                break;
            case "xrefs-to-system-api":
                com.sop.jadxxrefs.commands.XrefsCommand.xrefsToSystemApi(cmdArgs);
                break;
            case "search-classes":
                com.sop.jadxxrefs.commands.SearchCommand.searchClasses(cmdArgs);
                break;
            case "get-smali":
                com.sop.jadxxrefs.commands.SmaliCommand.getSmali(cmdArgs);
                break;
            case "inspect-class":
                com.sop.jadxxrefs.commands.InspectCommand.inspectClass(cmdArgs);
                break;
            case "debug-list-classes":
                com.sop.jadxxrefs.commands.DebugCommand.listClasses(cmdArgs);
                break;
            default:
                System.err.println("Unknown command: " + command);
                printUsage();
                throw new CommandException();
        }
    }

    private static void printUsage() {
        java.lang.System.out.println("Usage: java -jar jadx-xrefs-cli.jar <command> [options]");
        java.lang.System.out.println();
        java.lang.System.out.println("Commands:");
        java.lang.System.out.println("  xrefs-to-method   - Find all callers of a method");
        java.lang.System.out.println("  xrefs-to-class    - Find all references to a class");
        java.lang.System.out.println("  xrefs-to-field    - Find all references to a field");
        java.lang.System.out.println("  xrefs-to-system-api - Find all callers of a system API (bypass obfuscation)");
        java.lang.System.out.println("  search-classes    - Search classes by keyword");
        java.lang.System.out.println("  get-smali         - Get Smali code of a class");
        java.lang.System.out.println("  inspect-class     - Show methods and fields of a class");
        java.lang.System.out.println("  debug-list-classes - List loaded classes (debug)");
        java.lang.System.out.println();
        java.lang.System.out.println("Use '<command> --help' for command-specific options");
    }
}
