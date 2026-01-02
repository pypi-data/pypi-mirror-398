import yaml
import sys, re, os, socket, glob
import tlog.tlogging as tl
import tutils.thpe as thpe
import tio.tfile as tf
import unittest

log = tl.log

GIT_WORKSPACE = "C:\\usr\\ssz\\workspace\\git\\app"

UT = unittest.TestCase()


def exercise_lib_tfile_handler():
    log.info("exercise_lib_tfile_handler")
    # print(tf.diff("root@192.168.50.246:/ssz_share/eIUM_release_patchs", verbose=True))
    UT.assertFalse(tf.is_binary_file("package.json"))
    UT.assertFalse(tf.is_binary_file("index.ts"))
    for file_name in tf.listdir(
        f"{GIT_WORKSPACE}\\applications\\sourcecode\\shared\\rpcWebServer", True
    ):
        UT.assertNotIn("\\", file_name)
    tf_url = (
        "https://de.vicp.net:58443/tempestwin/bulletin/-/raw/main/network/public_ip.txt"
    )
    UT.assertTrue(
        tf.is_binary_file(
            "https://de.vicp.net:58443/Shao/doc-template/-/tree/main/template/project/bo/snippet-test-resources/icon/dollar.svg"
        )
    )
    tf_file = (
        f"{GIT_WORKSPACE}\\applications\\sourcecode\\shared\\rpcWebServer\\pom.xml"
    )
    UT.assertFalse(tf.is_binary_file(tf_file))
    UT.assertFalse(tf.is_binary_file(tf_url))
    if os.path.exists(tf_file):
        UT.assertEqual(
            "<artifactId>rpcWebServer-common</artifactId>",
            tf.find_context_in_file(
                tf_file, "<artifactId>.+</artifactId>", expected_match_count=2
            ),
        )
        UT.assertGreaterEqual(
            len(tf.readlines(tf_file)), 1, f"{tf_file} should not be empty"
        )
    if os.path.exists(
        f"{GIT_WORKSPACE}\\applications\\sourcecode\\shared\\rpcWebServer"
    ):
        pom_file_list = tf.search(
            f"{GIT_WORKSPACE}\\applications\\sourcecode\\shared\\rpcWebServer",
            "pom*.xml",
        )
        # pom*.xml,*可以是0-n长度的任意字符
        UT.assertGreaterEqual(
            len(pom_file_list),
            1,
            pom_file_list,
        )
        for pom_file in pom_file_list:
            UT.assertTrue(
                os.path.basename(pom_file).startswith("pom")
                and pom_file.endswith(".xml"),
                pom_file,
            )
    if not thpe.is_linux:
        UT.assertTrue(
            tf.match_exclude("D:\\git\\a.pdf", ["**/*.pdf"]),
            f"a.pdf should be excluded",
        )
    UT.assertTrue(
        tf.match_exclude("/git/a.pdf", ["**/*.pdf"]), f"a.pdf should be excluded"
    )
    UT.assertGreaterEqual(len(tf.readlines(tf_url)), 1, f"{tf_url} should not be empty")
    tf_url = "https://www.baidu.com"
    UT.assertGreaterEqual(len(tf.readlines(tf_url)), 1, f"{tf_url} should not be empty")
    if os.path.exists("C:\\git\\snap.rtc"):
        UT.assertEqual(
            "C:\\git\\snap.rtc",
            tf.left_folder_by_first("\\git\\snap.rtc\\cmbuild", "cmbuild/build.xml"),
        )
    if os.path.exists("C:\\git\\ium-dev"):
        ns = {"ium": "http://ov.hp.com/ium/namespace/plugin"}
        tf_attrib_list = tf.xml_attribs(
            "C:\\git\\ium-dev\\siu\\plugins\\com.hp.usage.mts\\plugin.xml.template",
            "ium:requires/ium:import",
            ns,
        )
        UT.assertGreaterEqual(
            len(tf_attrib_list), 1, f"tf_attrib_list should not be empty"
        )
        UT.assertIn(
            "plugin",
            tf_attrib_list[0],
            tf_attrib_list,
        )
    tf_attrib_dict = tf.xml_properties('<property name="compile.version" value="1.7"/>')
    UT.assertGreaterEqual(len(tf_attrib_dict), 1, tf_attrib_dict)
    UT.assertEqual("compile.version", tf_attrib_dict["name"], tf_attrib_dict)

    user_profile = f"C:\\Users\\ssz\\AppData\\Roaming\\Code\\User"
    if os.path.exists(user_profile):
        UT.assertIn("snippets", list_listdir := tf.listdir(user_profile), list_listdir)
        # 只有 /**, recursive=True才会生效, /*, 它并不生效
        UT.assertIn(
            os.path.join(user_profile, "snippets"),
            list_glob := [
                f
                for f in glob.glob(user_profile + "/**", recursive=False)
                if os.path.isdir(f)
            ],
            list_glob,
        )
        UT.assertIn(
            os.path.join(user_profile, "snippets"),
            list_glob := [
                f
                for f in glob.glob(os.path.join(user_profile, "**"), recursive=True)
                if os.path.isdir(f)
            ],
            list_glob,
        )
        UT.assertIn(
            os.path.join(user_profile, "globalStorage", "alefragnani.project-manager"),
            list_glob,
            list_glob,
        )
        # '*/globalStorage/alefragnani', ' */snippets', '*/settings.json'
        UT.assertTrue(
            tf.match(
                os.path.join(user_profile, "snippets"),
                include_array=[
                    "*/globalStorage/alefragnani",
                    "*/snippets",
                    "*/settings.json",
                ],
            ),
        )
    raw_local_file = tf.USE_LOCAL_FILE_FOR_DOC_TEMPLATE
    tf.USE_LOCAL_FILE_FOR_DOC_TEMPLATE = True
    tf_url = "https://de.vicp.net:58443/Shao/doc-template/-/raw/main/template/solution/db/build/pom.xml"
    UT.assertGreaterEqual(
        len(tf.readlines_from_http(tf_url)), 1, f"{tf_url} should not be empty"
    )
    tf.USE_LOCAL_FILE_FOR_DOC_TEMPLATE = raw_local_file
