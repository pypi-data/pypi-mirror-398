# -*- coding: utf-8 -*-
"""
    sphinxcontrib.plot
    ~~~~~~~~~~~~~~~~~~~~~

    An extension providing a reStructuredText directive .. plot:: for including a plot in a Sphinx document.

    See the README file for details.

    :author: Yongping Guo <guoyoooping@163.com>
    :license: MIT
"""

import re, os, sys
import posixpath
from os import path
import shutil
import copy
from subprocess import Popen, PIPE
from PIL import Image
import shlex
import imghdr

try:
    # Python 2.
    from StringIO import StringIO
    # Python 3.
except ImportError:
    from io import StringIO

try:
    from hashlib import sha1 as sha
except ImportError:
    from sha import sha

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.errors import SphinxError
from sphinx.util import ensuredir, relative_uri

OUTPUT_DEFAULT_FORMATS = dict(html='svg', latex='pdf', text=None)
OWN_OPTION_SPEC = dict( {
    #Use it as outfile instead of guess.
    #'image': str,
    #Caption of the generated figure.
    'caption': str,
    #include the script instead of the inline script. You must make sure it's readable.
    'include': str,
    #Control the output image size for gnuplot.
    'size': str,
    'magick': str,
    'show_source': str,
    'hidden': str,
    'latex_show_max_png': int,
    #'background': str,
    })

def plot_get_output_suffix (app, plot):
    '''
    suffix1: output of the cmd, 命令输出的原始文件
    suffix2: final output, 有些格式不支持在.pdf中显示，所以转换为.pdf 或者
             .png, 所以可以理解为latex的输出格式
    '''
    #默认
    args = shlex.split(plot['cmd'])
    text = plot['text']
    options = plot['total_options']

    #Caculate orig_suffix
    orig_suffix = OUTPUT_DEFAULT_FORMATS.get(app.builder.format, "png")
    if args[0] in ["imagemagick", "convert", "magick", "montage"]:
        #imagemagick: get the suffix of the last word not in the comments
        for i in reversed(StringIO(text).readlines()):
            if i and (not (i.lstrip().startswith('#'))):
                orig_suffix = i.split(".")[-1]
                break
    elif "ditaa" in args[0]:
        #ditaa 的输出默认为svg
        if not ("--svg" in args):
            args.insert(1, "--svg")
        orig_suffix = "svg"
    elif args[0] in ["seqdiag", "blockdiag", "actdiag", "nwdiag", "dot"]:
        #seqdiag, dot, If it's given -Tsvg, use it, or use svg.
        found = False
        for param in args:
            if "-T" in param:
                orig_suffix = param[2:]
                found = True
                break
        if (not found):
            # 如果用户没有设置-T参数，默认设置-Tsvg
            args.append("-Tsvg")
            plot['cmd'] = ' '.join(args)
            orig_suffix = "svg"
    elif args[0] == "gnuplot":
        #gnuplot的工作目录为目标原始文档的根目录
        if (app.builder.format == "html"):
            orig_suffix = "svg"
        elif (app.builder.format == "latex"):
            orig_suffix = "pdf"
    elif args[0] in ["dwebp", "cwebp"]:
        #dwebp, cwebp: -o 后面的参数是输出文件名
        if "-o" in args:
            index = args.index('-o')
            orig_suffix = args[index + 1].split(".")[-1]
    elif args[0] in ["python"]:
        #python: 临时用png, 事实上可以和gnuplot一样。
        orig_suffix = 'png'
    else:
        #默认情况下取最后一个字符做为输出文件名
        orig_suffix = args[-1].split(".")[-1]

    #Caculate the final_suffix, it's orig_suffix by default
    final_suffix = orig_suffix
    if options.get("magick", None):
        #如果用户指定了注释参数，输出文件始终为.png
        final_suffix = 'png'
    elif (app.builder.format == "html"):
        #通常情况下, 原始格式就是html的输出格式
        final_suffix = orig_suffix
    elif (app.builder.format == "latex"):
        if (orig_suffix == "gif"):
            #.gif 文件在latex里转换为.png格式
            final_suffix = 'png'
        elif (orig_suffix == "svg"):
            #.svg 文件在latex里转换为.pdf格式
            final_suffix = 'pdf'
        elif (orig_suffix == "webp"):
            #.webp 文件在latex里转换为.png格式
            final_suffix = 'png'
        elif (orig_suffix == "avif"):
            #.avif 文件在latex里转换为.jpg格式
            final_suffix = 'jpg'

    return (orig_suffix, final_suffix)

def plot_pre_process (app, plot, out):
    '''
    考虑到可能运行在cygwin下调用windows的原生命令，所以一律采用相对路径以避免
    路径问题
    1) 切换到正确的工作目录
    2) 生成infiles
    3) 生成args list
    '''
    cmd = plot['cmd']
    args = shlex.split(cmd)
    text = plot['text']
    options = plot['total_options']
    #rel_imgpath = relative_uri(app.builder.env.docname, app.builder.imagedir)
    #hashkey = str(cmd) + str(options) + str(plot['text'])
    #hashkey = sha(hashkey.encode('utf-8')).hexdigest()

    suffix = out["outfname"].split(".")[-1]
    infname = out['infname']
    infullfn = out['infullfn']
    outfullfn = out['outfullfn']
    outfname = out['outfname']
    ensuredir(path.join(app.builder.outdir, app.builder.imagedir))

    if "ditaa" in cmd:
        #ditaa 的工作目录为目标image所在的目录
        os.chdir(os.path.dirname(out["outfullfn"]))
        print("cd %s" %(os.getcwd()))

        #ditaa support vector/Chinese output by --svg parameter.
        if not ("--svg" in args):
            args.insert(1, "--svg")
        args.extend([infname, outfname])
    elif "seqdiag" in cmd or "blockdiag" in cmd \
            or "actdiag" in cmd or "nwdiag" in cmd:
        #seqdiag 的工作目录为目标image所在的目录
        os.chdir(os.path.dirname(out["outfullfn"]))
        print("cd %s" %(os.getcwd()))

        #seqdiag support vector output by -Tsvg parameter.
        if (suffix in ["svg", "pdf"]) and ("-Tsvg" not in cmd):
            args.insert(1, "-Tsvg")
        args.extend([infname, '-o', outfname])
    elif args[0] in ["inkscape", "svg"]:
        #gnuplot的工作目录为目标原始文档的根目录
        # The text is in .svg, so just copy it out.
        args = ["cp", infullfn, outfullfn]
    elif args[0] == "gnuplot":
        #gnuplot的工作目录为目标原始文档的根目录
        #if (not options.get("image", None)):
        #    #Don't change the text if image option is given
        #    size = options.get("size", "900,600")
        #    if (suffix in ["pdf", "eps"]):
        #        # pdf unit is inch while png is pixel, convert them.
        #        size = ",".join("%d" %(int(i.strip())/100) for i in size.split(","))
        lines = StringIO(text).readlines()
        # Remove the lines with set output/set terminal
        lines = [l for l in lines if (not re.search("^[^#]*set\s+output",
            l, flags=0)) and (not re.search("^[^#]*set\s+term", l, flags=0))]
        lines.insert(0, 'set output "%s"\n' %(out["outfullfn"]))
        terminal = (suffix == "png") and "pngcairo" or suffix
        lines.insert(0, 'set terminal %s\n' %(terminal))
        text = ''.join(lines)
        args.append(infullfn)
    elif args[0] == "dot":
        #dot的工作目录为目标原始文档的根目录：dot -Tpng in_file -o out_file
        args.extend([infullfn, '-o', out["outfullfn"]])
    elif args[0] in ["imagemagick", "convert", "magick", "montage", "dwebp"]:
        #形如这样的命令重要的是替换到目标文件：
        #dwebp _static/palms.webp -o palms.png
        tmp = []
        if text:
            args = ["sh", infullfn]
        else:
            #Only have command and not body: call args directly.
            args[-1] = out["outfullfn"]
            text = " ".join(args)
    elif args[0] in ["python"]:
        #For example: python
        args.append(infullfn)
    elif args[0] in ["wget", "curl"]:
        #For example: python
        target = os.path.basename(args[-1]).strip()
        if path.isfile("_static/%s" %(target)):
            #print("args: %s" %(args))
            args.clear()
            args.append("cp")
            args.append("_static/%s" %(target))
            args.append(target)
            #print("args2: %s" %(args))
        else:
            args.append("-O")
            args.append(target)

    #Write the text into infile if text is not empty
    if text:
        # write the text as infile.
        print("writing %s" %(infullfn))
        with open(infullfn, 'wb') as f:
            f.write(text.encode('utf-8'))

    #if app.builder.config.plot_log_level > 1:
    #    print("%s(), args: %s" %(sys._getframe().f_code.co_name, args))
    return args

def plot_process (args):
    '''
    调用shell命令生成图像
    '''
    # 2) generate the output file
    try:
        print(' '.join(args))
        p = Popen(args, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        stdout, stderr = (p.stdout.read(), p.stderr.read())
        if stdout:
            print("[1;30m%s[0m" %(stdout.decode(errors='ignore')))
        if stderr:
            print("[31m%s[0m" %(stderr.decode(errors='ignore')))
    except OSError as err:
        print("[31mError in call: %s.[0m" %(args))
        raise PlotError('[1;31m%s[0m' %(err))

def plot_post_process (app, plot, out):
    '''
    先从脚本或者命令出提取出输出文件名，再将其转化成out里的正式输出文件名。
    '''
    cmd = plot['cmd']
    args = shlex.split(cmd)
    text = plot['text']

    if (args[0] in ["ditaa", "dot", "seqdiag", "blockdiag", "actdiag", \
            "nwdiag", "inkscape", "svg", "gnuplot"]):
        #gnuplot write the outfile into the text. Others use outfile as -o
        #output.
        if app.builder.config.plot_log_level > 1:
            print("%s(), nothing to do and return." %(sys._getframe().f_code.co_name))
        return

    #if app.builder.config.plot_log_level > 1:
    #    print("%s(), text: %s." %(sys._getframe().f_code.co_name, text))
    #    print("%s(), cmd: %s." %(sys._getframe().f_code.co_name, cmd))

    if text:
        #从脚本中提取出输出文件名
        for i in reversed(StringIO(text).readlines()):
            #print("i1: %s" %(i))
            if i and (not (i.lstrip().startswith('#'))):
                intermediate_outfile = i.split()[-1]
                break
    else:
        #从命令中提取出输出文件名
        for i in reversed(StringIO(cmd).readlines()):
            #print("i2: %s" %(i))
            if i and (not (i.lstrip().startswith('#'))):
                intermediate_outfile = os.path.basename(i.split()[-1])
                #print("intermediate_outfile: %s." %(intermediate_outfile))
                break

    if args[0] in ["wget", "curl"] and \
            (not path.isfile("_static/%s" %(intermediate_outfile))):
        #第一次的时候，将wget/curl 下载的文件保存到_static/
        print("cp %s _static/" %(intermediate_outfile))
        os.system("cp %s _static/" %(intermediate_outfile))
        #将wget 下载的文件保存下来，避免每次需要下载
    print("mv %s %s" %(intermediate_outfile, out["outfullfn"]))
    os.system("mv %s %s" %(intermediate_outfile, out["outfullfn"]))

def plot_out1_2_out2 (app, plot, out1, out2):
    '''
    生成的图像有时候需要转换成另一种格式，例如latex不支持.svg, 要将它们转成
    .pdf格式
    '''
    #考虑到可能运行在cygwin下调用windows的原生命令，所以一律采用相对路径
    options = plot['total_options']
    os.chdir(os.path.dirname(out1["outfullfn"]))
    tmppath = os.getcwd()
    print("pwd: %s" %(tmppath))

    src = out1["outfname"]
    dst = out2["outfname"]
    src_suffix = os.path.splitext(src)[-1]
    dst_suffix = os.path.splitext(dst)[-1]
    if app.builder.config.plot_log_level >= 2:
        print("%s(),src: %s(%s), dst: %s(%s)"
                %(sys._getframe().f_code.co_name, src, src_suffix, dst, dst_suffix))

    if src_suffix == ".svg" and dst_suffix in [".pdf", ".png"]:
        #.svg --> .pdf
        inkscape = os.system("which inkscape 2> /dev/null")
        if inkscape != 0:
            print('[1;31minkscape does not exist, isntall it at first[0m')
        inkscape = os.popen("inkscape --version | awk  '{print $2}'") 
        if (int(inkscape.read().split(".")[0], 10) >= 1):
            print("inkscape %s -o %s" %(src, dst))
            os.system("inkscape %s -o %s" %(src, dst))
        else:
            print("inkscape -f %s -A %s" %(src, dst))
            os.system("inkscape -f %s -A %s" %(src, dst))
    elif (src_suffix == ".webp") and (dst_suffix == ".png"):
        #.webp --> .png
        print("dwebp %s -o %s" %(src, dst))
        os.system("dwebp %s -o %s" %(src, dst))
    elif (src_suffix == ".avif") and (dst_suffix == ".jpg"):
        #.webp --> .jpg
        print("ffmpeg -i %s %s" %(src, dst))
        os.system("magick %s %s" %(src, dst))
    elif src_suffix == ".gif" and dst_suffix == ".png":
        #.gif --> .png
        png_nums =  options.get("latex_show_max_png", 8)
        i = Image.open(src)
        #n = list(ImageSequence.Iterator(i)).size()
        max_num = (i.n_frames > 16) and 16 or i.n_frames
        #print("i: %d, max_num: %d"  %(i.n_frames, max_num))
        print("montage %s[0-%d] -coalesce -tile %dx %s" 
                %(src, max_num - 1, png_nums, dst))
        os.system("montage %s[0-%d] -coalesce -tile %dx %s" 
                %(src, max_num - 1, png_nums, dst))
        if max_num < i.n_frames:
            #在图片最后写个"..."提示有截短
            os.system("convert %s -gravity southeast -annotate +0+0 '...' %s"
                    %(dst, dst))

        #print("options: %s" %(options))
        #如果.gif 指定了width, 需要为它加倍以免最终的图片太小看不清
        if options.get("width", None) and ("%" in options["width"]):
            options.pop("width")
        elif options.get("width", None):
            #print("options: %s" %(options))
            options["width"] = int(options["width"]) * png_nums
            #print("options: %s" %(options))
        os.system("rm %s" %(src))
    else:
        #rename
        print("error? mv %s %s" %(src, dst))
        os.system("mv %s %s" %(src, dst))

def plot_add_annotate (app, plot, out2):
    '''
    生成的图像有时候需要转换成另一种格式，例如latex不支持.svg, 要将它们转成
    .pdf格式
    '''
    options = plot['total_options']
    suffix = os.path.splitext(out2["outrelfn"])[-1]
    if app.builder.config.plot_log_level >= 2:
        print("%s() add magick," %(sys._getframe().f_code.co_name))

    # We'd like to add magick onto the output.
    c = "magick %s" %(out2["outfullfn"])
    for i in StringIO(options["magick"]).readlines():
        if (i.lstrip()[0] != "#"):
            c += " %s" %(i.strip().rstrip("\\"))
    c += " %s" %(out2["outfullfn"])
    print(c)
    os.system(c)

def plot_get_image_width(img, filename):
    '''
    对于png, jpg, gif 文件，手动获取它的大小
    '''
    i = Image.open(filename)
    if img.get("scale", None):
        width = "%d" %(i.width * img["scale"] / 100)
    elif (not img.get("width", None)) and \
            (not img.get("width", None)):
        #Mainly for latex, give width if there is not.
        width = "%d" %(i.width)
    else:
        width = img["width"]

    #print("get image %s width: %s." %(filename, width))
    return width

def plot_text_2_image (app, plot):
    """
    1) 解析plot的内容, 最重要的是解析生成文件的后缀名。
    2) 判断是不是已经做过。如果已经做过，直接返回结果，避免重复调用。
    3) 将解析的结果根据options加以处理
    Render plot code into a PNG output file.
    """
    cmd = plot['cmd']
    args = shlex.split(cmd)
    text = plot['text']
    options = plot['total_options']

    rel_imgpath = relative_uri(app.builder.env.docname, app.builder.imagedir)
    hashkey = str(cmd) + str(options) + str(plot['text'])
    hashkey = sha(hashkey.encode('utf-8')).hexdigest()
    infname = '%s-%s.%s' % (os.path.basename(args[0]), hashkey, plot['directive'])
    infullfn = path.join(app.builder.outdir, app.builder.imagedir, infname)

    #确保目标路径存在，如果不存在就创建一个
    ensuredir(path.join(app.builder.outdir, app.builder.imagedir))
    (suffix1, suffix2) = plot_get_output_suffix(app, plot)

    #这个是中间文件，可能需要再转化一下才是最终的格式
    outfname1 = '%s-%s.%s' %(os.path.basename(args[0]), hashkey, suffix1)
    out1 = dict(infname = infname,
            infullfn = infullfn,
            outfname = outfname1,
            outrelfn = posixpath.join(rel_imgpath, outfname1),
            outfullfn = path.join(app.builder.outdir, app.builder.imagedir, outfname1),
            outreference = None)

    #这个是最终的生成文件
    outfname2 = '%s-%s.%s' %(os.path.basename(args[0]), hashkey, suffix2)
    out2 = dict(infname = infname,
            infullfn = infullfn,
            outfname = outfname2,
            outrelfn = posixpath.join(rel_imgpath, outfname2),
            outfullfn = path.join(app.builder.outdir, app.builder.imagedir, outfname2),
            outreference = None)
    if app.builder.config.plot_log_level > 1:
        print("out1: %s" %(out1))
        print("out2: %s" %(out2))

    #Generate the image by system call
    if path.isfile(out2["outfullfn"]):
        print("file existed: %s" %(outfname2))
        return out2

    #有些命令需要修改当前路径，所以提前记下来一会儿恢复
    currpath = os.getcwd()
    args = plot_pre_process(app, plot, out1)
    plot_process(args)
    plot_post_process(app, plot, out1)
    if outfname1 != outfname2:
        #中间文件和最后的文件不同，需要转换一次
        plot_out1_2_out2(app, plot, out1, out2)

    if options.get("magick", None):
        plot_add_annotate(app, plot, out2)

    if options.get("show_source", False):
        out2["outreference"] = posixpath.join(rel_imgpath, infname)

    #回到原来的目录
    os.chdir(currpath)

    #if app.builder.config.plot_log_level > 1:
    #    print("%s(), out2: %s" %(sys._getframe().f_code.co_name, out2))
    return out2

class PlotError(SphinxError):
    category = 'plot error'

class PlotDirective(directives.images.Figure):
    """
    扫描文档时如果找到..plot:: 命令后建议一个空的figure对象，并且将.. plot::
    的内容保存在figure对象上。
    """
    has_content = True
    required_arguments = 0
    option_spec = directives.images.Figure.option_spec.copy()
    option_spec.update(OWN_OPTION_SPEC)

    def plot_param_parser(self, content, options):
        '''
        Given content and return the parsed dictionary:
        {"cmd": xxx, "text": xxx, "option": xxx, "total_options": xxx}
        '''
        tmp = ""
        for line in content:
            #Find the fist verb not starting with '#'
            if (line and (not line.lstrip().startswith('#'))):
                tmp = line.split()[0]
                #if not options.get("caption", None):
                #    #If no :caption: is given, take the 1st line as caption.
                #    tmp_line = line.rstrip()
                #    if tmp_line[-1] == "\\":
                #        options["caption"] = tmp_line[:-1] + "..."
                #    else:
                #        options["caption"] = tmp_line
                break
        if (tmp in ["imagemagick", "convert", "magick", "montage"]):
            #in case convert and montage: we put the cmd into the text itself
            cmd = tmp
            if len(content[0].split()) > 1:
                #所有的命令在命令行上
                text = '\n'.join(content)
            else:
                #命令行为convert, 所有的命令在内容里
                text = '\n'.join(content[1:])
        else:
            cmd = content[0]
            #There is a empty line between command and inlne script, remove it.
            text = '\n'.join(content[2:])

        total_options = options.copy()
        if total_options.get("include", None):
            #Use :include: if it's given
            if path.isfile(total_options["include"]):
                include_filename = total_options.pop("include")
                #print("include_filename: %s" %(include_filename))
                with open(include_filename,'r') as f:
                    text = f.read()
            else:
                #:include: is given but not readable
                print("[31mWARNING: :include: %s is given but not readable!!![0m"
                        %(total_options["include"]))
                return None
        #print("total_options: %s" %(total_options))
        #print("cmd: %s" %(cmd))
        #print("text: %s" %(text))

        own_options = dict([(k,v) for k,v in total_options.items() 
                                  if k in OWN_OPTION_SPEC])
        dic = dict(cmd=cmd,text=text,options=own_options,
                directive="plot", total_options=total_options)
        return dic
  
    def run(self):
        '''
        将.. plot:: 的内容和参数保存到figure对象的.plot成员里以备后用。
        '''
        self.arguments = ['']
        params = self.plot_param_parser(self.content, self.options)

        # Remove the own options from self-options which will be as figure
        # options.
        for x in params["options"].keys():
            self.options.pop(x)
        # don't parse the centent as legend, it's not legend.
        self.content = None

        #Create a empty image or figure object from self.
        if ("alt" in params["total_options"].keys()):
            #If there is alt parameters then it's inline image
            (node,) = directives.images.Image.run(self)
        else:
            #Figure
            (node,) = directives.images.Figure.run(self)
        if isinstance(node, nodes.system_message):
            return [node]

        node.plot = dict(**params)
        #print("PlotDirective.run(), note: %s" %(node))
        return [node]

# http://epydoc.sourceforge.net/docutils/
def doctree_read_callback(app, doctree):
    uris = dict();

    #第一次遍历，生成inline image
    for img in doctree.traverse(nodes.image):
        #For candidate
        if not hasattr(img, 'plot'):
            if app.builder.config.plot_log_level > 1:
                print("%s(), img: %s" %(sys._getframe().f_code.co_name, img))
            continue

        print("----------------------------------------------------------------")
        if app.builder.config.plot_log_level > 0:
            print("%s(), img plot cmd: %s, alt: %s"
                    %(sys._getframe().f_code.co_name,
                        (hasattr(img, 'plot')) and img.plot['cmd'] or None,
                        img.get('alt', None)))
        text = img.plot['text']
        options = img.plot['options']
        cmd = img.plot['cmd']
        try:
            #生成图像, 再把图像的地址链接到image的uri里, 这样就是显示在文档里了
            out = plot_text_2_image(app, img.plot)
            if options.get("hidden", False) or (not path.isfile(out["outfullfn"])):
                #Don't render the image if there is hidden
                nodes.image.pop(img)
                continue
            img['uri'] = out["outrelfn"]
            if img.get('alt', None):
                #用于类似这样的调用:.. |test1| plot:: convert in.jpg -flop out.jpg
                uris[img['alt']] = img['uri']
            if os.path.splitext(out["outfullfn"])[-1] in [".png",".jpg",".gif"]:
                img["width"] = plot_get_image_width(img, out["outfullfn"])
            #img['candidates']={'*': out["outrelfn"]}
            if out["outreference"]:
                reference_node = nodes.reference(refuri=out["outreference"])
                img.replace_self(reference_node)
                reference_node.append(img) 
        except PlotError as err:
            print(err)
            img.replace_self(nodes.literal_block("", "%s\n%s" %(cmd, text)))
            continue
        if app.builder.config.plot_log_level > 0:
            print("%s(), img: %s" %(sys._getframe().f_code.co_name, img))
            print("uris: %s" %(uris))

    #第二次遍历，解析inline image
    for img in doctree.traverse(nodes.image):
        if (not hasattr(img, 'plot')) and img.get('alt', None) and \
                (img['alt'] in uris.keys()):
            img['uri'] = uris[img['alt']]
            #img['candidates'] = {'*': uris[img['alt']]}
            print("------------------------------------------------------------")
            print("inline uri = %s" %(img['uri']))

    for fig in doctree.traverse(nodes.figure):
        if not hasattr(fig, 'plot'):
            if app.builder.config.plot_log_level > 1:
                print("%s(), img: %s" %(sys._getframe().f_code.co_name, img))
            continue
        print("================================================================")
        cmd = fig.plot['cmd']
        text = fig.plot['text']
        options = fig.plot['options']
        #print("options: %s" %(options))

        try:
            #生成图像, 再把图像的地址链接到figure的uri里, 这样就是显示在文档里了
            out = plot_text_2_image(app, fig.plot)
            if options.get("hidden", False) or (not path.isfile(out["outfullfn"])):
                #Don't render the image if there is hidden
                nodes.figure.pop(fig)
                continue

            #Caption
            if options.get("caption", None):
                fig += nodes.caption("", options.get("caption", cmd))
            fig['ids'] = ["plot"]

            #uri
            for img in fig.traverse(condition=nodes.image):
                img['uri'] = out["outrelfn"]
                if out["outreference"]:
                    reference_node = nodes.reference(refuri=out["outreference"])
                    reference_node += img
                    fig.replace(img, reference_node)
                if os.path.splitext(out["outfullfn"])[-1] in [".png",".jpg",".gif"]:
                    img["width"] = plot_get_image_width(img, out["outfullfn"])
        except PlotError as err:
            #app.builder.warn('plot error: ')
            print(err)
            fig.replace_self(nodes.literal_block("", "%s\n%s" %(cmd, text)))
            continue
        if app.builder.config.plot_log_level > 0:
            print("%s(), fig: %s" %(sys._getframe().f_code.co_name, fig))

def setup(app):
    #注册2个回调函数
    app.add_directive('plot', PlotDirective)
    app.connect('doctree-read', doctree_read_callback)

    app.add_config_value('plot', 'plot', 'html')
    app.add_config_value('plot_args', [], 'html')
    #plot_log_level, 0: don't print debug info; 1: only print in parameters
    #and out result. 2: debug info
    app.add_config_value('plot_log_level', 0, 'html')
    app.add_config_value('plot_output_format', OUTPUT_DEFAULT_FORMATS, 'html')

#References
###########

#. reStructuredText and Sphinx Reference, https://documatt.com/restructuredtext-reference/element/figure.html
