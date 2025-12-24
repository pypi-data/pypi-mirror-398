from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

def graph2d_(allVertics, cov_vertics):
        '''The Graphing function: it is a class function- private'''

        #extact 2 points index from the cov list as [0,1]; [2,3]; [4,5]; ...
        i = 0
        inx_covxHull_vertic = [] #list of coupled indexs 
        for inx in range(len(cov_vertics)):
             if i == len(cov_vertics):
                 break
             inx_covxHull_vertic.append([i, i+1])
             i+=2
        
        # extract x, and y for the ALL vertics
        x = [p[0] for p in allVertics]
        y = [p[1] for p in allVertics]

        # generate the pdf
        with PdfPages("output.pdf") as pdf:

            # Create a wide figure for side-by-side layout
            fig, (ax_table, ax_plot) = plt.subplots(1, 2, figsize=(12, 5))

            # -------------------------
            # LEFT SIDE: TABLE
            # -------------------------
            ax_table.axis("off")

            table_data = [[p[0], p[1]] for p in cov_vertics]
            table = ax_table.table(
                cellText=table_data,
                colLabels=["X", "Y"],
                loc="center",
                cellLoc="center"
            )
            table.scale(1.2, 1.2)
            ax_table.set_title("ConvexHull Vertices- by: Deniz DAHMAN, PhD")

            # -------------------------
            # RIGHT SIDE: SCATTER PLOT
            # -------------------------
            ax_plot.scatter(x, y, color="blue")
            for ix in inx_covxHull_vertic: #connect the vertix line
                ver1 = cov_vertics[ix[0]]
                ver2 = cov_vertics[ix[1]]
                combinedVer = [ver1, ver2]
                x_conv = [p[0] for p in combinedVer]
                y_conv = [p[1] for p in combinedVer]
                ax_plot.plot(x_conv, y_conv, marker="o")
            ax_plot.set_xlabel("X")
            ax_plot.set_ylabel("Y")
            ax_plot.set_title("Scatter Plot of ConvexHull- by: Deniz DAHMAN, PhD")
            ax_plot.grid(True)
        
            # Save the page
            pdf.savefig(fig)
            plt.close(fig)
            print("Operation of drawing the ConvexHull is successful. Check [output.pdf] file at the current path")
