import os
import shutil
from dataclasses import dataclass, field
import cv2
import pathlib
import numpy as np
import umap
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
import pandas as pd
from types import SimpleNamespace

from havoc_clustering_v2.general_utility.ai.tileextractor import TileExtractor
from havoc_clustering_v2 import correlation_of_dlfv_groups
from havoc_clustering_v2.general_utility import unique_colors
from havoc_clustering_v2.feature_extractor import FeatureExtractor


# from general_utility.ai.tileextractor import TileExtractor
# import correlation_of_dlfv_groups
# from general_utility import unique_colors
# from feature_extractor import FeatureExtractor


@dataclass(slots=True)
class DeveloperOptions:
    save_and_keep_tmp_tiles: bool = False
    save_csv_gz: bool = False  # compressed file. ~2x storage reduction
    map_scale_fac: int = 16
    use_presaved: bool = False  # skips DLFV generation. assumes DLFV/thumbnail file exists already


@dataclass(slots=True)
class HAVOCConfig:
    out_dir: str = './'
    k_vals: list[int] = field(default_factory=lambda: [7, 8, 9])  # if empty [], only performs feature extraction
    save_tiles_k_vals: list[int] = field(default_factory=list)

    tile_size: int = 512

    min_tissue_amt: float = 0.2

    extra_metrics: list[str] = field(default_factory=lambda: ['umap', 'dendrogram', 'corr_clustmap'])

    # Developer-only section
    dev: DeveloperOptions = field(default_factory=DeveloperOptions, repr=False)

    def __post_init__(self):
        if not set(self.save_tiles_k_vals).issubset(self.k_vals):
            raise ValueError("save_tiles_k_vals must be a subset of k_vals")

        if self.tile_size % 256 != 0:
            raise ValueError("tile_size must multiple of 256")

        if not (0.0 <= self.min_tissue_amt <= 1.0):
            raise ValueError("min_tissue_amt must be between 0 and 1")

        if not set(self.extra_metrics).issubset(['umap', 'dendrogram', 'corr_clustmap']):
            raise ValueError("invalid extra_metrics")


class HAVOC:

    def __init__(self, havoc_config: HAVOCConfig):
        self.config = havoc_config
        if havoc_config.dev.use_presaved:
            self.feature_extractor = SimpleNamespace(num_features=1536)
        else:
            self.feature_extractor = FeatureExtractor()
        self.save_tiles = bool(havoc_config.save_tiles_k_vals) or havoc_config.dev.save_and_keep_tmp_tiles
        self.Z = None  # linkage. calculated in code

        pathlib.Path(havoc_config.out_dir).mkdir(parents=True, exist_ok=True)

    def run(self, slide):

        if slide.mpp is None:
            raise Exception("Slide MPP not detected. Please create slide object with explicit MPP")

        curr_out_dir = os.path.join(self.config.out_dir, slide.name)
        pathlib.Path(curr_out_dir).mkdir(parents=True, exist_ok=True)

        if not self.config.dev.use_presaved:
            df, thumbnail = self.process_dlfvs(slide, curr_out_dir=curr_out_dir)
        else:
            df = pd.read_csv(os.path.join(curr_out_dir, 'cluster_info_df.csv'))
            thumbnail = TileExtractor(slide, self.config.tile_size, map_scale_fac=self.config.dev.map_scale_fac)
            thumbnail = thumbnail.extraction_map
            thumbnail.image = cv2.imread(os.path.join(curr_out_dir, 'thumbnail.jpg'))

        # remove all the previously clustered columns (if applicable)
        df = df.loc[:, ~df.columns.str.match(r"^k\d+(_|$)")]

        if len(self.config.k_vals):
            # Build full hierarchy once...full tree
            self.Z = linkage(df[[str(x) for x in range(1, self.feature_extractor.num_features + 1)]], method='ward')

            cluster_info_df = self.create_cluster_info_df()
            df = pd.concat([cluster_info_df, df], axis=1)

        df.to_csv(os.path.join(curr_out_dir, 'cluster_info_df.csv'), index=False)
        if self.config.dev.save_csv_gz:
            df.to_csv(os.path.join(curr_out_dir, 'cluster_info_df.csv.gz'), index=False, compression="gzip")

        ### result generation ###
        if len(self.config.k_vals):
            self.create_colortiled_slide(df, thumbnail, curr_out_dir=curr_out_dir)

            if 'dendrogram' in self.config.extra_metrics:
                self.make_dendrogram(df, curr_out_dir=curr_out_dir)
            if 'umap' in self.config.extra_metrics:
                self.make_umap(df, curr_out_dir=curr_out_dir)

            if 'corr_clustmap' in self.config.extra_metrics:
                for k in self.config.k_vals:
                    correlation_of_dlfv_groups.create_correlation_clustermap_single_slide(curr_out_dir, target_k=k)

        if self.save_tiles and not self.config.dev.save_and_keep_tmp_tiles:
            # done copying to k color folders
            shutil.rmtree(os.path.join(curr_out_dir, 'tiles', 'tmp'))

    def process_dlfvs(self, slide, curr_out_dir):

        if self.save_tiles:
            # we save all the tiles to a tmp folder and then copy the tiles into color folders when we do colortiling
            pathlib.Path(os.path.join(curr_out_dir, 'tiles', 'tmp')).mkdir(parents=True, exist_ok=True)

        print(f'Processing {slide.name}...')

        te = TileExtractor(slide, self.config.tile_size, map_scale_fac=self.config.dev.map_scale_fac)
        gen = te.iterate_tiles2(min_tissue_amt=self.config.min_tissue_amt, batch_size=4)

        coors = []
        dlfvs = []
        amt_tissues = []
        for res in gen:
            tiles, currcoors, amt_tissue = res['tiles'], res['coordinates'], res['amt_tissue']

            currdlfvs = self.feature_extractor.process(tiles)
            # currdlfvs = np.zeros((tiles.shape[0],1536))

            coors.append(currcoors)
            dlfvs.append(currdlfvs)
            amt_tissues.append(amt_tissue)

            if self.save_tiles:
                # each iteration contains a batch of tiles
                for pos in range(len(tiles)):
                    curr_sp = os.path.join(curr_out_dir, 'tiles', 'tmp', str(tuple(currcoors[pos].tolist())) + '.jpg')
                    cv2.imwrite(curr_sp, tiles[pos])

        # we go through the whole slide so the extraction map is slide's thumbnail
        cv2.imwrite(os.path.join(curr_out_dir, 'thumbnail.jpg'), te.extraction_map.image)

        dlfvs = np.concatenate(dlfvs)
        coors = np.concatenate(coors)
        amt_tissues = np.concatenate(amt_tissues)

        df = pd.DataFrame(dlfvs, columns=[str(x) for x in range(1, self.feature_extractor.num_features + 1)])
        df[['coor_x1_20x', 'coor_y1_20x', 'coor_x2_20x', 'coor_y2_20x']] = coors
        df['amt_tissue'] = [round(x, 4) for x in amt_tissues]

        return df, te.extraction_map

    # cluster the data into k groups and assign each a (stable, incremental) color
    def create_cluster_info_df(self):

        k_vals = sorted(self.config.k_vals)
        k_min = k_vals[0]
        k_max = k_vals[-1]

        # 2) Get labels for all k in one shot
        labels_per_k: dict[int, np.ndarray] = {}
        for k in k_vals:
            # fcluster returns labels 1..k; convert to 0..k-1
            labels = fcluster(self.Z, t=k, criterion="maxclust") - 1
            labels_per_k[k] = labels

        # 3) Global color generator (from your RGB_COLORS list)
        color_gen = unique_colors.next_color_generator(
            scaled=False,
            mode="rgb",
            shuffle=False,
        )

        # (k, cluster_id) -> {'name': ..., 'val': (r,g,b)}
        cluster_color: dict[tuple[int, int], dict] = {}

        # 4) Initialize colors at the smallest k (e.g., k=2)
        k_prev = k_min
        labels_prev = labels_per_k[k_prev]

        # sort clusters at k_min by size (largest first)
        counts_prev = np.bincount(labels_prev, minlength=k_prev)
        cluster_ids_sorted = np.argsort(counts_prev)[::-1]

        for cid in cluster_ids_sorted:
            color_info = next(color_gen)
            cluster_color[(k_prev, cid)] = color_info

        # 5) For each larger k, propagate and introduce new colors on splits
        for k in k_vals[1:]:
            labels_curr = labels_per_k[k]
            counts_curr = np.bincount(labels_curr, minlength=k)

            # Map each current cluster -> its parent cluster at k_prev
            parent_for_child: dict[int, int] = {}
            for c in range(k):
                mask = (labels_curr == c)
                # Because of hierarchy, this should be exactly one parent
                parent_ids = np.unique(labels_prev[mask])
                if parent_ids.size != 1:
                    # Safety check; in theory this shouldn't happen
                    raise RuntimeError(
                        f"Cluster {c} at k={k} has multiple parents at k={k_prev}: {parent_ids}"
                    )
                parent_for_child[c] = int(parent_ids[0])

            # Group children by parent
            parent_to_children: dict[int, list[int]] = {}
            for c, p in parent_for_child.items():
                parent_to_children.setdefault(p, []).append(c)

            # Assign colors for this k
            for p, children in parent_to_children.items():
                parent_color = cluster_color[(k_prev, p)]

                if len(children) == 1:
                    # No split: child keeps parent's color
                    c = children[0]
                    cluster_color[(k, c)] = parent_color
                else:
                    # Parent split into multiple children:
                    # - largest child keeps parent's color
                    # - others get new colors from palette
                    children_sorted = sorted(
                        children,
                        key=lambda c: counts_curr[c],
                        reverse=True
                    )

                    # Largest child inherits the parent's color
                    first = True
                    for c in children_sorted:
                        if first:
                            cluster_color[(k, c)] = parent_color
                            first = False
                        else:
                            cluster_color[(k, c)] = next(color_gen)

            # Move to next k
            k_prev = k
            labels_prev = labels_curr

        # 6) Build DataFrame with Cluster_k and color columns for all k
        dfs = []
        for k in k_vals:
            labels_k = labels_per_k[k]
            temp_df = pd.DataFrame({f"k{k}": labels_k})

            color_name_col = []
            color_rgb_col = []
            for lbl in labels_k:
                color_info = cluster_color[(k, lbl)]
                color_name_col.append(color_info["name"])
                color_rgb_col.append(color_info["val"])

            temp_df[f"k{k}_color"] = color_name_col
            temp_df[[f"k{k}_color_r", f"k{k}_color_g", f"k{k}_color_b"]] = np.array(color_rgb_col)

            dfs.append(temp_df)

        # 7) Concatenate all k-level cluster columns side-by-side
        cluster_info_df = pd.concat(dfs, axis=1)

        return cluster_info_df

    def create_colortiled_slide(self, cluster_info_df, thumbnail, curr_out_dir):
        '''
        Using a dict mapping cluster to coordinates, creates bordered boxes all throughout the image.
        Optionally, save the tiles belonging to each color cluster
        '''

        coor_cols = ['coor_x1_20x', 'coor_y1_20x', 'coor_x2_20x', 'coor_y2_20x']

        for k in self.config.k_vals:
            rgb_cols = [f'k{k}_color_r', f'k{k}_color_g', f'k{k}_color_b']

            # make the color folders for saving the actual tiles
            if k in self.config.save_tiles_k_vals:
                for c in cluster_info_df[f'k{k}_color'].unique():
                    pathlib.Path(os.path.join(curr_out_dir, 'tiles', str(k), c)).mkdir(parents=True, exist_ok=True)

                    coords = cluster_info_df[coor_cols][cluster_info_df[f'k{k}_color'] == c]
                    for x1, y1, x2, y2 in coords.itertuples(index=False):
                        fname = f"({x1}, {y1}, {x2}, {y2}).jpg"
                        try:
                            shutil.copy2(os.path.join(curr_out_dir, 'tiles', 'tmp', fname),
                                         os.path.join(curr_out_dir, 'tiles', str(k), c, fname))
                        except FileNotFoundError:
                            print(f'Tile for coordinate {x1, y1, x2, y2} not found')

            # group on cluster color and get all the associated coordinates
            for color, coors in cluster_info_df.groupby(rgb_cols)[coor_cols].apply(
                    lambda d: list(map(tuple, d.to_numpy()))).items():
                # change rgb to bgr
                thumbnail.add_borders(coors, color=color[::-1], border_thickness=0.1)

            cv2.imwrite(
                os.path.join(curr_out_dir, f'k{k}_colortiled.jpg'),
                thumbnail.image
            )

    def make_umap(self, cluster_info_df, curr_out_dir):

        print('Generating UMAP')

        reducer = umap.UMAP(
            random_state=42,
            n_components=2,
            metric="cosine"  # optional but recommended for embeddings
        )
        res = reducer.fit_transform(
            cluster_info_df[[str(x) for x in range(1, self.feature_extractor.num_features + 1)]]
        )
        umap_df = pd.DataFrame({'X': res[:, 0], 'Y': res[:, 1]})

        for k in self.config.k_vals:
            rgb_cols = [f'k{k}_color_r', f'k{k}_color_g', f'k{k}_color_b']
            umap_df[rgb_cols] = cluster_info_df[rgb_cols]

            # go through each cluster and get the data belonging to it. plot it with its corresponding color
            plt.close('all')
            for (r, g, b), rows in umap_df.groupby(rgb_cols):
                color = (r / 255.0, g / 255.0, b / 255.0)  # matplotlib expects 0–1 floats

                plt.scatter(
                    rows["X"],
                    rows["Y"],
                    s=20,
                    c=[color]  # one color per group
                )

            sp = os.path.join(curr_out_dir, f'k{k}_umap.jpg')
            plt.savefig(sp, dpi=200, bbox_inches='tight')

    def make_dendrogram(self, cluster_info_df, curr_out_dir):

        print('Generating dendrogram')

        Z = self.Z
        n = Z.shape[0] + 1  # number of leaves

        for k in self.config.k_vals:
            rgb_cols = [f'k{k}_color_r', f'k{k}_color_g', f'k{k}_color_b']

            # Build leaf-id -> hex color mapping
            # ASSUMPTION: cluster_info_df is indexed by leaf id 0..n-1
            rgb = (
                cluster_info_df.loc[np.arange(n), rgb_cols]
                .to_numpy(dtype=np.uint8)
            )

            leaf_hex = {
                i: f"#{r:02x}{g:02x}{b:02x}"
                for i, (r, g, b) in enumerate(rgb)
            }

            link_cols = {}
            for i, (a, b) in enumerate(Z[:, :2].astype(int)):
                c1 = link_cols[a] if a >= n else leaf_hex[a]
                c2 = link_cols[b] if b >= n else leaf_hex[b]
                link_cols[n + i] = c1 if c1 == c2 else "#0000FF"

            plt.close("all")
            plt.title("Hierarchical Clustering Dendrogram")
            plt.ylabel("distance")

            dendrogram(
                Z,
                no_labels=True,
                color_threshold=None,
                link_color_func=lambda k: link_cols[k],
            )

            sp = os.path.join(curr_out_dir, f'k{k}_dendrogram.jpg')
            plt.savefig(sp, dpi=200, bbox_inches='tight')
