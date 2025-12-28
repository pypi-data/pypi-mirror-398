import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import os
from typing import Union
from sklearn.decomposition import PCA
from mpl_toolkits.mplot3d import Axes3D




def nulls(data:pd.DataFrame, column:Union[str, int]) -> None:
    """
    Analyzes and prints the number and percentage of null values in a specified column of a DataFrame.

    This function calculates the total count and percentage of missing (null) values in a given column 
    of a Pandas DataFrame. The results are displayed in a formatted string.

    Args:
        data (pd.DataFrame): The input DataFrame containing the data to analyze.
        column (str or int): The name of the column to check for null values.

    Returns:
        None: The function directly prints the analysis results.

    Features:
        - Calculates the total number of null values in the specified column using `isnull()`.
        - Computes the percentage of null values relative to the total number of rows in the DataFrame.
        - Displays the results in a clear, formatted string with column name, null count, and percentage.

    Example:
        Analyzing a single column:
         import pandas as pd
         df = pd.DataFrame({'A': [1, None, 3, 4], 'B': [None, None, 3, 4]})
         nulls(df, 'A')
        Column: A                              Amount of nulls: 1            Percentage of nulls: 25.00 %
        
        Analyzing multiple columns:
         for column in df.columns:
        ...     nulls(df, column)
        Column: A                              Amount of nulls: 1            Percentage of nulls: 25.00 %
        Column: B                              Amount of nulls: 2            Percentage of nulls: 50.00 %

    Notes:
        - If the column name provided does not exist in the DataFrame, the function will raise a KeyError.
        - The function assumes the input data is a valid Pandas DataFrame.

    Limitations:
        - The function does not handle cases where the DataFrame is empty. Ensure the DataFrame has data before use.
        - Works on one column at a time. For analyzing multiple columns, use a loop as shown in the example.

    Customizations:
        - To handle missing values programmatically instead of printing results, return the calculated null count and percentage.
    """

    nulls_ = data[column].isnull().sum()
    percentage = round(nulls_/len(data)*100, 2)
    print(f'Column: {column:30}   Amount of nulls: {nulls_:<10}   Percentage of nulls: {percentage:.2f} %')



def outliers(data:pd.DataFrame, column:Union[str, int], title:str="Descriptive Statistics", color:str='violet', fig_size:tuple[int, int]=(15,5), visualization:bool=True, return_dict:bool=False) -> Union[dict, None]:
    """
    Analyzes numerical outliers in a specified column of a DataFrame, providing
    optional visualizations and optionally returning descriptive statistics.

    This function performs a statistical analysis of a numerical column, including
    quartiles, central tendency metrics, dispersion measures, and outlier detection
    based on the IQR method. When enabled, it also generates visualizations
    (histogram, boxplot, and a textual statistics panel).

    Args:
        data (pd.DataFrame): Input DataFrame containing the data to analyze.
        column (str or int): Column name or index to analyze. Must be numeric or
            convertible to numeric.
        title (str): Title for the statistics subplot. Defaults to
            "Descriptive Statistics".
        color (str): Color used for the histogram and boxplot. Defaults to 'violet'.
        fig_size (tuple[int, int]): Size of the figure used for visualizations.
            Defaults to (15, 5).
        visualization (bool): If True, generates plots and displays statistics
            visually. If False, skips all visual output. Defaults to True.
        return_dict (bool): If True, returns a dictionary with computed statistics
            instead of returning None. Defaults to False.

    Returns:
        dict or None:
            - If `return_dict` is True, returns a dictionary containing:
                mean, median, mode, quartiles (Q1–Q4), standard deviation, IQR,
                upper and lower outlier limits, total data count, and outlier count.
            - If `return_dict` is False, returns None.

    Features:
        - Converts the selected column to numeric, coercing non-numeric values to NaN.
        - Computes descriptive statistics and IQR-based outlier thresholds.
        - Identifies outliers beyond 1.5 * IQR.
        - Optionally generates:
            1. Histogram with KDE.
            2. Boxplot.
            3. Textual summary of statistics in a third subplot.
        - Drops NaN values before all statistical calculations.

    Example:
        import pandas as pd
        df = pd.DataFrame({'A': [1, 2, 2, 3, 100]})
        outliers(df, column='A')

        Returning statistics without plots:
        stats = outliers(df, column='A', visualization=False, return_dict=True)

        For multiple numeric columns:
        for col in df.select_dtypes(include='number').columns:
            outliers(df, column=col)

    Notes:
        - The column must contain numeric data or be coercible to numeric.
        - If the column is empty or contains only NaN values after coercion,
          no statistics or plots are generated.
        - When `visualization` is False, the function performs calculations only.

    Limitations:
        - Intended for numerical analysis only.
        - Mode is computed using pandas and may return the first mode if multiple exist.

    """

    data[column] = pd.to_numeric(data[column], errors='coerce')

    
    if visualization:
        fig, axes = plt.subplots(1, 3, figsize=fig_size) 
        fig.suptitle(f'Analysis for column {column}')
        sns.histplot(data=data, x=column, kde=True, ax=axes[0], color=color)
        axes[0].set_title('Distribution')
        sns.boxplot(data=data, y=column, ax=axes[1], color=color)
        axes[1].set_title('Boxplot')

  
    serie = data[column].dropna()
    if not serie.empty:
        min = np.min(serie)
        max = np.max(serie)
        q1 = np.percentile(serie, 25)
        q2 = np.percentile(serie, 50)  
        q3 = np.percentile(serie, 75)
        q4 = np.percentile(serie, 100) 
        mean = np.mean(serie)
        median = np.median(serie)
        mode = serie.mode()[0] if not serie.mode().empty else "No mode"
        std = np.std(serie)
        iqr = q3 - q1
        tlo = q3 + 1.5*iqr
        blo = q1 - 1.5*iqr
        
        oq = serie[(serie > tlo) | (serie < blo)].count()

        if visualization:
            step = 0.082
            y = 0.9
            axes[2].text(0.1, y, f'Min: {min:.4f}', transform=axes[2].transAxes); y -= step
            axes[2].text(0.1, y, f'Max: {max:.4f}', transform=axes[2].transAxes); y -= step
            axes[2].text(0.1, y, f'Q1: {q1:.4f}', transform=axes[2].transAxes); y -= step
            axes[2].text(0.1, y, f'Q2: {q2:.4f}', transform=axes[2].transAxes); y -= step
            axes[2].text(0.1, y, f'Q3: {q3:.4f}', transform=axes[2].transAxes); y -= step
            axes[2].text(0.1, y, f'Q4: {q4:.4f}', transform=axes[2].transAxes); y -= step
            axes[2].text(0.1, y, f'Mean: {mean:.4f}', transform=axes[2].transAxes); y -= step
            axes[2].text(0.1, y, f'Median: {median:.4f}', transform=axes[2].transAxes); y -= step
            axes[2].text(0.1, y, f'Mode: {mode:.4f}', transform=axes[2].transAxes); y -= step
            axes[2].text(0.1, y, f'Std: {std:.4f}', transform=axes[2].transAxes); y -= step
            axes[2].text(0.1, y, f'IQR: {iqr:.4f}', transform=axes[2].transAxes); y -= step
            axes[2].text(0.1, y, f"Top Limit Outliers: {tlo:.4f}", transform=axes[2].transAxes); y -= step
            axes[2].text(0.1, y, f"Bottom Limit Outliers: {blo:.4f}", transform=axes[2].transAxes); y -= step
            axes[2].text(0.1, y, f"Total Data: {len(data)}", transform=axes[2].transAxes); y -= step
            axes[2].text(0.1, y, f"Outliers Quantity: {oq} ({round(oq/len(data)*100, 2)})%", transform=axes[2].transAxes)

            axes[2].set_title(title)
            axes[2].axis('off')  
            plt.tight_layout()
            plt.show()
            plt.close(fig)

        if return_dict:
            return {
                'mean': round(mean,4), 'median': round(median,4), 'mode': round(mode,4),
                'Q1': round(q1,4), 'Q2': round(q2,4), 'Q3': round(q3,4), 'Q4': round(q4,4),
                'STD': round(std,4), 'IQR': round(iqr,4),
                'Top Limit Outliers': round(tlo,4), 'Bottom Limit Outliers': round(blo,4),
                'Total Data': len(data), 'Outliers Quantity': oq
            }



def heatmap_correlation(data:pd.DataFrame, columns:list, title:str='', output_dir:str='', name:str='Heatmap', correlation_type:str='spearman', fig_size:tuple[int, int]=(12,10), cmap:str='coolwarm', linewidths:float=0.5, fontsize:int=10, fontsize_title:int=14, show:bool=True, save:bool=False) -> None:
    """
    Generates and optionally saves a heatmap of correlation values for selected columns in a DataFrame.

    This function computes the correlation matrix for the specified columns using the chosen 
    correlation method ('pearson' or 'spearman') and visualizes it as a heatmap. The plot 
    can be saved to a specified directory or displayed interactively. 

    **Note**: The specified columns must contain numeric data. Non-numeric columns should be excluded 
    from the correlation analysis beforehand.

    Args:
        data (pd.DataFrame): The input DataFrame containing the data to analyze.
        columns (list): A list of column names (must be numeric) to include in the correlation analysis.
        title (str): The title of the heatmap.
        output_dir (str): The directory where the heatmap image will be saved, if `save` is True. 
            Defaults to an empty string (current working directory).
        name (str): The name of the saved image file (without extension). Defaults to 'Heatmap'.
        correlation_type (str): The type of correlation to compute ('pearson' or 'spearman'). 
            Defaults to 'spearman'.
        fig_size (tuple[int, int]): The size of the figure. Defaults to (12, 10).
        cmap (str): The colormap for the heatmap. Defaults to 'coolwarm'.
        linewidths (float): The width of the lines separating cells in the heatmap. Defaults to 0.5.
        fontsize (int): The font size for tick labels. Defaults to 10.
        fontsize_title (int): The font size for the title. Defaults to 14.
        show (bool): Whether to display the heatmap interactively. Defaults to True.
        save (bool): Whether to save the heatmap as an image file. Defaults to False.

    Returns:
        None: The function either displays the heatmap interactively or saves it as an image file.

    Raises:
        ValueError: If `correlation_type` is not 'pearson' or 'spearman', or if any of the 
            specified columns are not present in the DataFrame.

    Example:
         import pandas as pd
         import numpy as np
         df = pd.DataFrame(np.random.rand(100, 4), columns=['A', 'B', 'C', 'D'])
         heatmap_correlation(
        ...     data=df, 
        ...     columns=['A', 'B', 'C', 'D'], 
        ...     title='Correlation Heatmap', 
        ...     output_dir='./plots', 
        ...     name='heatmap_example', 
        ...     correlation_type='pearson', 
        ...     show=True, 
        ...     save=True
        ... )
    """

    df = data[columns]
    if correlation_type == 'pearson':
        correlacion = df.corr(method='pearson')
    elif correlation_type == 'spearman':
        correlacion = df.corr(method='spearman')
    else:
        raise ValueError("The correlation type must be 'pearson' or 'spearman'.")
    plt.figure(figsize=fig_size)
    sns.heatmap(correlacion, annot=True, cmap=cmap, linewidths=linewidths, annot_kws={"size": 10}, 
                cbar_kws={"shrink": .8}, fmt=".2f", center=0)
    plt.xticks(fontsize=fontsize, rotation=45, ha='right')
    plt.yticks(fontsize=fontsize, rotation=0)
    plt.title(title, fontsize=fontsize_title)
    plt.tight_layout()
    if save:
        output_path = os.path.join(output_dir, f'{name}.png')
        plt.savefig(output_path)
    if show:
        plt.show() 
    if save or show:
        plt.close()





def pca_view(data:pd.DataFrame, dimensions:int, target:Union[str, int]=None, title:str='', scaler:any = None, fig_size:tuple[int, int]=(8, 8), visualization:bool=False, return_target:bool=False) -> pd.DataFrame:
    """
    Performs Principal Component Analysis (PCA) on a DataFrame and optionally visualizes the results.

    The function applies PCA to reduce the dimensionality of the dataset, and its behavior is determined
    by the `return_target` and `dimensions` parameters:
    
    - If `return_target=False`, PCA is applied only to the features, and the scatter plot shows only the 
      principal components.
    - If `return_target=True`, the output DataFrame includes the target variable, and the scatter plot 
      will include the target as part of the visualization.

    **Note**: The function scales the features if a scaler (e.g., StandardScaler) is provided.

    **Dimensions Restriction**: Only 2 or 3 dimensions are supported for visualization. If a number different from 2 or 3 is passed for `dimensions`, an error will be raised.

    Args:
        data (pd.DataFrame): The input DataFrame containing the data to analyze.
        dimensions (int): The number of dimensions (2 or 3) to retain in the PCA.
        target (str or int, optional): The column name or index of the target variable. If None, no target will be used in visualization.
        title (str): Title for the scatter plot.
        scaler (optional): A scaler object (e.g., StandardScaler) to scale the features before PCA. Defaults to None.
        fig_size (tuple[int, int]): Figure size for visualization. Defaults to (8, 8).
        visualization (bool): Whether to visualize the PCA results (2D or 3D). Defaults to False.
        return_target (bool): Determines the structure of the output and visualization:
            - If False: PCA is applied only on features, and the scatter plot shows only the components.
            - If True: The output DataFrame includes the target variable, and the scatter plot includes target as part of the visualization.

    Returns:
        pd.DataFrame: A DataFrame with the principal components and, optionally, the target variable.

    Raises:
        ValueError: If `dimensions` is not 2 or 3.
        KeyError: If the specified target column does not exist in the DataFrame.
        TypeError: If `scaler` is not an object with a `fit_transform` method.

    Examples:
        Example 1: PCA without target, 2 components for visualization
         import pandas as pd
         from sklearn.preprocessing import StandardScaler
         df = pd.DataFrame(np.random.rand(100, 5), columns=['A', 'B', 'C', 'D', 'target'])
         scaler = StandardScaler()
         pca_result = pca_view(df, dimensions=2, target='target', scaler=scaler, visualization=True, return_target=False)
        # Output: A 2D scatter plot of PC1 vs PC2, showing only the components.

        Example 2: PCA with target, 2 components for visualization
         pca_result = pca_view(df, dimensions=2, target='target', scaler=scaler, visualization=True, return_target=True)
        # Output: A 2D scatter plot of PC1 vs PC2, with points colored by the target variable.

        Example 3: PCA with target, 3 components for visualization
         pca_result = pca_view(df, dimensions=3, target='target', scaler=scaler, visualization=True, return_target=True)
        # Output: A 3D scatter plot of PC1, PC2, PC3, with points colored by the target variable.

        Example 4: PCA without target, 3 components for visualization
         pca_result = pca_view(df, dimensions=3, target='target', scaler=scaler, visualization=True, return_target=False)
        # Output: A 3D scatter plot of PC1, PC2, PC3, showing only the components.
        
    Use Cases:
        - **When to use `return_target=False`**:
            - Useful when you only care about the relationship between features, independent of any target variable.
            - Ideal for visualizing general patterns or clusters based on the features alone (e.g., embeddings, feature-based clustering).
            - Example: Reducing dimensionality for visualization of large datasets without focusing on a target variable.

        - **When to use `return_target=True`**:
            - Suitable when you want to understand the distribution of the target variable with respect to the principal components.
            - Great for identifying patterns related to specific target values (e.g., classes in classification problems).
            - Example: Understanding how the target variable (e.g., disease presence, class labels) is distributed across the principal components.
    """
          
    if dimensions not in [2, 3]:
        raise ValueError('Dimensions must be either 2 or 3.')
    if target is not None:
        X = data.drop(columns=[target])
        y = data[target]
    else:
        X = data
        y = None
    if scaler:
        X_scaled = scaler.fit_transform(X)
    else:
        X_scaled = X.values
    if return_target and y is not None:
        pca_model = PCA(n_components=dimensions-1)  
    else:
        pca_model = PCA(n_components=dimensions)
    X_pca = pca_model.fit_transform(X_scaled)
    df_pca = pd.DataFrame(X_pca, columns=[f'PC{i+1}' for i in range(X_pca.shape[1])])
    if return_target and y is not None:
        df_pca[target] = y
    if visualization:
        plt.figure(figsize=fig_size)
        if return_target and y is not None:
            if dimensions == 2:
                plt.scatter(df_pca['PC1'], df_pca[target], c=y, cmap='viridis')
                plt.xlabel('PC1')
                plt.ylabel(target)
                plt.colorbar(label=target)  
            elif dimensions == 3:
                ax = plt.axes(projection='3d')
                scatter = ax.scatter(df_pca['PC1'], df_pca['PC2'], df_pca[target], c=y, cmap='viridis')
                ax.set_xlabel('PC1')
                ax.set_ylabel('PC2')
                ax.set_zlabel(target)  
                plt.colorbar(scatter, label=target)
        else:
            if dimensions == 2:
                plt.scatter(df_pca['PC1'], df_pca['PC2'], c='blue')
                plt.xlabel('PC1')
                plt.ylabel('PC2')
            elif dimensions == 3:
                ax = plt.axes(projection='3d')
                ax.scatter(df_pca['PC1'], df_pca['PC2'], df_pca['PC3'], c='blue')
                ax.set_xlabel('PC1')
                ax.set_ylabel('PC2')
                ax.set_zlabel('PC3')
        plt.title(title)
        plt.show()
    return df_pca


if __name__ == '__main__':
    print('EDA module: includes functions for null check, outlier detection, correlation maps and PCA visualization. Designed for data exploration.')
   
